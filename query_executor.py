import sqlite3
import pandas as pd

def run_sql_query(sql_query: str, db_path="d:/AgenticRAG/chinook.db"):
    try:
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query(sql_query, conn)
        conn.close()
        return df
    except Exception as e:
        return f"Error executing SQL: {e}"
