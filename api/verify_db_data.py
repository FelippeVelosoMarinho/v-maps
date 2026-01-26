import asyncio
import sys
from sqlalchemy import select
from app.database import async_session
from app.models.map import Map
from app.models.group import Group, GroupMap, GroupMember
from app.models.user import User

async def dump_data():
    async with async_session() as db:
        print("=== MAPS ===")
        result = await db.execute(select(Map))
        for m in result.scalars().all():
            print(f"Map: {m.id} | Name: {m.name} | Owner: {m.created_by}")

        print("\n=== GROUPS ===")
        result = await db.execute(select(Group))
        for g in result.scalars().all():
            print(f"Group: {g.id} | Name: {g.name}")

        print("\n=== GROUP MAPS ===")
        result = await db.execute(select(GroupMap))
        for gm in result.scalars().all():
            print(f"GroupMap: Map {gm.map_id} <-> Group {gm.group_id}")

        print("\n=== GROUP MEMBERS ===")
        result = await db.execute(select(GroupMember))
        for gm in result.scalars().all():
            print(f"GroupMember: Group {gm.group_id} <-> User {gm.user_id}")

if __name__ == "__main__":
    # Fix for Windows asyncio loop policy if needed, though usually fine in simple script
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(dump_data())
