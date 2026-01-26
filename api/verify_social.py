import asyncio
import httpx
import sys

BASE_URL = "http://localhost:8000"

async def verify_social():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # 1. Login to get token (assuming test user exists or we can use a known email/password)
        # Note: In a real environment, we'd create a test user. 
        # Here I'll just check if the endpoints exist by making requests that might 401 but confirm the route.
        
        print("--- Testing /social/feed ---")
        response = await client.get("/social/feed")
        print(f"Feed response (expected 401 if not logged in): {response.status_code}")
        
        print("\n--- Testing /social/favorites ---")
        response = await client.get("/social/favorites")
        print(f"Favorites response (expected 401 if not logged in): {response.status_code}")

        # Let's check the health
        response = await client.get("/health")
        print(f"Health check: {response.json()}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(verify_social())
