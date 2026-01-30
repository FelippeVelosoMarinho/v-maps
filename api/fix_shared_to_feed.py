import asyncio
from sqlalchemy import text
from app.database import engine

async def fix_db():
    async with engine.begin() as conn:
        print("Checking and adding shared_to_feed columns...")
        
        # Add shared_to_feed to maps
        try:
            await conn.execute(text("ALTER TABLE maps ADD COLUMN shared_to_feed BOOLEAN DEFAULT FALSE"))
            print("Added shared_to_feed to maps")
        except Exception as e:
            print(f"Maps column might already exist or error: {e}")

        # Add shared_to_feed to trips
        try:
            await conn.execute(text("ALTER TABLE trips ADD COLUMN shared_to_feed BOOLEAN DEFAULT FALSE"))
            print("Added shared_to_feed to trips")
        except Exception as e:
            print(f"Trips column might already exist or error: {e}")

        # Add shared_to_feed to check_ins
        try:
            await conn.execute(text("ALTER TABLE check_ins ADD COLUMN shared_to_feed BOOLEAN DEFAULT FALSE"))
            print("Added shared_to_feed to check_ins")
        except Exception as e:
            print(f"Check-ins column might already exist or error: {e}")
            
    print("Database fix completed.")

if __name__ == "__main__":
    asyncio.run(fix_db())
