import sqlite3

def fix_users():
    try:
        conn = sqlite3.connect("fairshare_v2.db")
        cursor = conn.cursor()
        
        # Check if is_verified column exists first (it should after migration)
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if "is_verified" in columns:
            print("Verifying all existing users...")
            cursor.execute("UPDATE users SET is_verified = 1")
            print(f"Updated {cursor.rowcount} users.")
        else:
            print("Column 'is_verified' not found. Migration might not have run.")
            
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fix_users()
