import asyncio
import sqlite3
from datetime import datetime
import uuid

def test_insert():
    try:
        conn = sqlite3.connect('vmaps.db')
        cursor = conn.cursor()
        
        # Check if trip exists
        trip_id = "fc383436-1d0b-4d37-9aa1-0704084c3f1f"
        cursor.execute("SELECT id FROM trips WHERE id=?", (trip_id,))
        trip = cursor.fetchone()
        if not trip:
            print(f"Warning: Trip {trip_id} not found in database.")
        else:
            print(f"Trip {trip_id} found.")
            
        # Try to insert a message
        msg_id = str(uuid.uuid4())
        user_id = "some_user_id" # This might be any valid user id
        # Let's get a real user id first
        cursor.execute("SELECT id FROM users LIMIT 1")
        user = cursor.fetchone()
        if user:
            user_id = user[0]
            print(f"Using user_id: {user_id}")
            
            content = "Test message"
            created_at = datetime.utcnow().isoformat()
            
            print(f"Attempting to insert message {msg_id} with trip_id {trip_id}")
            cursor.execute(
                "INSERT INTO chat_messages (id, trip_id, user_id, content, created_at) VALUES (?, ?, ?, ?, ?)",
                (msg_id, trip_id, user_id, content, created_at)
            )
            print("Insert successful!")
            conn.commit()
        else:
            print("No users found in database.")
            
    except Exception as e:
        print(f"Error during insert: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    test_insert()
