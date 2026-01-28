
import sqlite3

conn = sqlite3.connect('fairshare_v2.db')
cursor = conn.cursor()

try:
    print("Adding 'start_location' column to 'trips' table...")
    cursor.execute("ALTER TABLE trips ADD COLUMN start_location TEXT")
    conn.commit()
    print("✅ Successfully added 'start_location' column.")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e).lower():
        print("ℹ️ 'start_location' column already exists.")
    else:
        print(f"❌ Error adding column: {e}")

conn.close()
