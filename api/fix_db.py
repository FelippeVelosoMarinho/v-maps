import sqlite3
import os

db_path = "vmaps.db"

if not os.path.exists(db_path):
    print(f"Database {db_path} not found.")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

tables_to_drop = [
    "_alembic_tmp_map_members",
    "_alembic_tmp_places",
    "_alembic_tmp_trip_participants"
]

for table in tables_to_drop:
    try:
        cursor.execute(f"DROP TABLE IF EXISTS {table}")
        print(f"Dropped {table}")
    except Exception as e:
        print(f"Error dropping {table}: {e}")

conn.commit()
conn.close()
print("Cleanup complete.")
