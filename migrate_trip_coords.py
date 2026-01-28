
import sqlite3

conn = sqlite3.connect('fairshare_v2.db')
cursor = conn.cursor()

def add_column(table, column, type):
    try:
        print(f"Adding '{column}' column to '{table}' table...")
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {type}")
        conn.commit()
        print(f"✅ Successfully added '{column}' column.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print(f"ℹ️ '{column}' column already exists.")
        else:
            print(f"❌ Error adding column '{column}': {e}")

add_column("trips", "latitude", "FLOAT")
add_column("trips", "longitude", "FLOAT")

conn.close()
