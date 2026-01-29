from sqlalchemy import create_engine, inspect
from database_sql import Base, engine
import sqlite3

def migrate_all():
    # Use inspector to get existing tables and columns
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    conn = sqlite3.connect("fairshare_v2.db")
    cursor = conn.cursor()
    
    # Iterate through all models in Base.metadata
    for table_name, table in Base.metadata.tables.items():
        if table_name not in existing_tables:
            print(f"Table {table_name} missing. Creating...")
            table.create(engine)
            continue
            
        # Get existing columns for this table
        existing_columns = [col['name'] for col in inspector.get_columns(table_name)]
        
        # Check for missing columns
        for column in table.columns:
            if column.name not in existing_columns:
                print(f"Adding column {column.name} to table {table_name}...")
                
                # Basic type mapping for SQLite
                col_type = str(column.type)
                if "VARCHAR" in col_type or "STRING" in col_type:
                    type_str = "TEXT"
                elif "INTEGER" in col_type:
                    type_str = "INTEGER"
                elif "FLOAT" in col_type:
                    type_str = "FLOAT"
                elif "BOOLEAN" in col_type:
                    type_str = "BOOLEAN"
                elif "DATETIME" in col_type:
                    type_str = "DATETIME"
                elif "TEXT" in col_type:
                    type_str = "TEXT"
                else:
                    type_str = "TEXT" # Fallback
                
                default_val = ""
                if column.default is not None:
                    # Very basic default extractor
                    if hasattr(column.default, 'arg'):
                        arg = column.default.arg
                        if isinstance(arg, (int, float)):
                            default_val = f" DEFAULT {arg}"
                        elif isinstance(arg, bool):
                            default_val = f" DEFAULT {1 if arg else 0}"
                
                try:
                    cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column.name} {type_str}{default_val}")
                    print(f"Successfully added {column.name} to {table_name}")
                except Exception as e:
                    print(f"Error adding {column.name} to {table_name}: {e}")
    
    conn.commit()
    conn.close()
    print("Migration check complete.")

if __name__ == "__main__":
    migrate_all()
