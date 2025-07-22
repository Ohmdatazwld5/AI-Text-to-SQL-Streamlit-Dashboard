import sqlite3
from config import DB_PATH

print("DB Path:", DB_PATH)
print("Exists:", DB_PATH.exists(), "Size:", DB_PATH.stat().st_size if DB_PATH.exists() else "N/A")

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
print("Tables:", cur.fetchall())
conn.close()


