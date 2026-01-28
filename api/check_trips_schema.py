import sqlite3

def check_trips_schema():
    conn = sqlite3.connect('vmaps.db')
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(trips)")
    columns = cursor.fetchall()
    print("Trips columns:")
    for col in columns:
        print(col)
    conn.close()

if __name__ == "__main__":
    check_trips_schema()
