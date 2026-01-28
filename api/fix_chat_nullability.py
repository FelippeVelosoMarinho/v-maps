import sqlite3
import uuid

def migrate_to_nullable_map_id():
    try:
        conn = sqlite3.connect('vmaps.db')
        cursor = conn.cursor()
        
        # 1. Get current columns and check them
        cursor.execute("PRAGMA table_info(chat_messages)")
        old_columns_info = cursor.fetchall()
        column_names = [info[1] for info in old_columns_info]
        print(f"Current columns: {column_names}")
        
        # 2. Create new table with correct schema
        # Note: We include trip_id which was added earlier
        cursor.execute("""
            CREATE TABLE chat_messages_new (
                id VARCHAR(36) PRIMARY KEY,
                map_id VARCHAR(36),
                trip_id VARCHAR(36),
                user_id VARCHAR(36) NOT NULL,
                content TEXT NOT NULL,
                created_at DATETIME NOT NULL,
                FOREIGN KEY(map_id) REFERENCES maps(id) ON DELETE CASCADE,
                FOREIGN KEY(trip_id) REFERENCES trips(id) ON DELETE CASCADE,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # 3. Copy data
        # Mapping old columns to new columns
        # We need to handle the case where trip_id might not have existed (though I added it)
        cols_to_copy = [c for c in column_names if c in ['id', 'map_id', 'trip_id', 'user_id', 'content', 'created_at']]
        cols_str = ", ".join(cols_to_copy)
        
        print(f"Copying data for columns: {cols_str}")
        cursor.execute(f"INSERT INTO chat_messages_new ({cols_str}) SELECT {cols_str} FROM chat_messages")
        
        # 4. Drop old table
        cursor.execute("DROP TABLE chat_messages")
        
        # 5. Rename new table
        cursor.execute("ALTER TABLE chat_messages_new RENAME TO chat_messages")
        
        # 6. Create indexes (optional but good practice as they were missing in my manual check)
        cursor.execute("CREATE INDEX idx_chat_messages_map_id ON chat_messages(map_id)")
        cursor.execute("CREATE INDEX idx_chat_messages_trip_id ON chat_messages(trip_id)")
        
        conn.commit()
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_to_nullable_map_id()
