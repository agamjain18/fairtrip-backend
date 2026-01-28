import sqlite3

def check_columns():
    conn = sqlite3.connect("fairshare_v2.db")
    cursor = conn.cursor()
    
    tables = ["users", "cities"]
    for table in tables:
        print(f"\nColumns in {table}:")
        try:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            for col in columns:
                print(f" - {col[1]} ({col[2]})")
        except Exception as e:
            print(f"Error checking {table}: {e}")
            
    conn.close()

if __name__ == "__main__":
    check_columns()
