import os
import re
import sqlite3
from dotenv import load_dotenv
from groq import Groq
from config import DB_PATH  # ensure_db already ran in config

load_dotenv()
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def get_schema_text():
    # Try to open DB; if we can't, return minimal schema hint so LLM doesn't hallucinate crazy joins
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t[0] for t in cur.fetchall()]
        parts = []
        for t in tables:
            cur.execute(f"PRAGMA table_info({t});")
            cols = [c[1] for c in cur.fetchall()]
            parts.append(f"{t}({', '.join(cols)})")
        conn.close()
        return "\n".join(parts) if parts else "(no schema read)"
    except Exception:
        return "(schema unavailable; valid Chinook tables include invoices, customers, invoice_items, tracks, albums, artists, genres)"

def _extract_sql(text: str) -> str:
    m = re.search(r"```(?:sql)?(.*?)```", text, flags=re.I | re.S)
    if m:
        candidate = m.group(1)
    else:
        m2 = re.search(r"(?is)\b(select|with)\b.*", text)
        candidate = text[m2.start():] if m2 else text

    lines = []
    for line in candidate.splitlines():
        s = line.strip()
        if s.startswith("--") or s.startswith("#") or s.startswith("```"):
            continue
        lines.append(line)
    sql = "\n".join(lines).strip()

    semi = sql.find(";")
    if semi != -1:
        sql = sql[:semi+1]
    if not sql.endswith(";"):
        sql += ";"
    return sql.strip()

def natural_to_sql(user_query: str) -> str:
    schema_text = get_schema_text()
    prompt = f"""
You are an expert SQL generator for the SQLite Chinook database.
Use ONLY the tables and columns shown below. If a needed field is in Customers, use Customer fields like Country, City, etc.
If country is requested, use Customers.Country or Invoices.BillingCountry (NOT Address tables).
If totals are needed, SUM(Invoices.Total) OR SUM(Invoice_Items.UnitPrice * Invoice_Items.Quantity).
Return ONLY executable SQL. No markdown. No prose.

Schema:
{schema_text}

User question: {user_query}
"""
    resp = groq_client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama3-70b-8192",
        temperature=0,
        max_tokens=300,
    )
    raw = resp.choices[0].message.content.strip()
    return _extract_sql(raw)




