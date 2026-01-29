
import sqlite3

conn = sqlite3.connect('fairshare_v2.db')
cursor = conn.cursor()

try:
    print("Adding 'popular_spots' column to 'cities' table...")
    cursor.execute("ALTER TABLE cities ADD COLUMN popular_spots JSON")
    conn.commit()
    print("✅ Successfully added 'popular_spots' column.")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e).lower():
        print("ℹ️ 'popular_spots' column already exists.")
    else:
        print(f"❌ Error adding column: {e}")

conn.close()
