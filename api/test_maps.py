import asyncio
import sys
import os
import traceback
import json

# Add current dir to path
sys.path.append(os.getcwd())

async def test_all():
    print("--- Testing Imports ---")
    try:
        from app.database import async_session
        from app.models import User, Map, SocialPost, Profile
        from app.routers.social import build_social_post_response
        print("Imports OK")
    except Exception:
        print("Import Failed!")
        traceback.print_exc()
        return

    print("\n--- Testing Database & Social Logic ---")
    try:
        async with async_session() as db:
            from sqlalchemy import select
            res = await db.execute(select(User).limit(1))
            user = res.scalar_one_or_none()
            if not user:
                print("No users found.")
                return
            
            print(f"User: {user.email}")
            
            # Test Social Feed logic
            from sqlalchemy import desc
            res = await db.execute(select(SocialPost).order_by(desc(SocialPost.created_at)).limit(5))
            posts = res.scalars().all()
            print(f"Found {len(posts)} social posts")
            
            for post in posts:
                print(f"  Building response for post {post.id} (type: {post.content_type})")
                try:
                    resp = await build_social_post_response(db, post, user.id)
                    print(f"    OK: {resp.id}")
                except Exception as e:
                    print(f"    FAILED: {e}")
                    traceback.print_exc()

    except Exception:
        print("Fatal error during test!")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_all())
