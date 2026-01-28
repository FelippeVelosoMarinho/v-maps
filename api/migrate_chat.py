import sqlite3

def migrate():
    conn = sqlite3.connect('vmaps.db')
    cursor = conn.cursor()
    
    # Check if trip_id already exists
    cursor.execute("PRAGMA table_info(chat_messages)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'trip_id' not in columns:
        print("Adding trip_id to chat_messages...")
        cursor.execute("ALTER TABLE chat_messages ADD COLUMN trip_id VARCHAR(36)")
        print("Successfully added trip_id.")
    else:
        print("trip_id already exists in chat_messages.")
        
    conn.commit()
    conn.close()

if __name__ == "__main__":
    migrate()
