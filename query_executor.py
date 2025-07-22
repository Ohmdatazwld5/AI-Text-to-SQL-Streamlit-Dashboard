import sqlite3
import pandas as pd
from config import DB_PATH  # already resolved by ensure_db

def run_sql_query(sql_query: str):
    try:
        # Connect read-only if file exists; else normal connect
        uri_path = f"file:{DB_PATH}?mode=ro" if DB_PATH.exists() else str(DB_PATH)
        conn = sqlite3.connect(uri_path, uri=DB_PATH.exists())
        df = pd.read_sql_query(sql_query, conn)
        conn.close()
        return df
    except Exception as e:
        return f"Error executing SQL: {e}"


