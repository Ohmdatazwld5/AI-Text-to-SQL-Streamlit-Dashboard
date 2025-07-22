import os
import re
import sqlite3
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# ----- schema helper (same as earlier, if not already in file) -----
def get_schema_text(db_path=r"d:\AgenticRAG\chinook.db"):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cur.fetchall()]
    parts = []
    for t in tables:
        cur.execute(f"PRAGMA table_info({t});")
        cols = [c[1] for c in cur.fetchall()]
        parts.append(f"{t}({', '.join(cols)})")
    conn.close()
    return "\n".join(parts)

# ----- extract clean SQL from LLM output -----
def _extract_sql(text: str) -> str:
    # Grab first fenced block ```sql ... ``` or ``` ... ```
    m = re.search(r"```(?:sql)?(.*?)```", text, flags=re.I | re.S)
    if m:
        candidate = m.group(1)
    else:
        # Fallback: from first SELECT or WITH onward
        m2 = re.search(r"(?is)\b(select|with)\b.*", text)
        candidate = text[m2.start():] if m2 else text

    # Drop comment lines & stray backticks
    lines = []
    for line in candidate.splitlines():
        s = line.strip()
        if s.startswith("--") or s.startswith("#") or s.startswith("```"):
            continue
        lines.append(line)
    sql = "\n".join(lines).strip()

    # Keep only up to first semicolon if multiple statements
    semi = sql.find(";")
    if semi != -1:
        sql = sql[:semi+1]

    # Ensure ends with ;
    if not sql.endswith(";"):
        sql += ";"

    return sql.strip()

def natural_to_sql(user_query: str, db_path=r"d:\AgenticRAG\chinook.db") -> str:
    schema_text = get_schema_text(db_path=db_path)
    prompt = f"""
You are an expert SQL generator for the SQLite Chinook database.
Only use these tables/columns:
{schema_text}

User question: {user_query}

Return ONLY executable SQL. No prose. No markdown. One statement.
"""
    resp = groq_client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama3-70b-8192",
        temperature=0,
        max_tokens=300,
    )
    raw = resp.choices[0].message.content.strip()
    clean = _extract_sql(raw)
    return clean


