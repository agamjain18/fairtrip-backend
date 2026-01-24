import sqlite3
import os

db_path = "fairshare.db"
if not os.path.exists(db_path):
    print(f"Database {db_path} not found")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables in fairshare.db:")
    for table in tables:
        print(f"- {table[0]}")
    conn.close()
