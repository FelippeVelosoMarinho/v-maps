from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Map, MapMember, GroupMap, GroupMember

async def check_map_access(db: AsyncSession, map_id: str, user_id: str) -> bool:
    """
    Check if a user has access to a map.
    Access is granted if:
    1. User is the creator of the map
    2. User is a direct member of the map
    3. User is a member of a group that is shared with the map
    
    Uses a single optimized query to verify all conditions.
    """
    
    # Query logic:
    # Select 1 from Map 
    # LEFT JOIN MapMember ON map.id = map_member.map_id AND map_member.user_id = user_id
    # LEFT JOIN GroupMap ON map.id = group_map.map_id
    # LEFT JOIN GroupMember ON group_map.group_id = group_member.group_id AND group_member.user_id = user_id
    # WHERE map.id = map_id
    # AND (map.created_by = user_id OR map_member.id IS NOT NULL OR group_member.id IS NOT NULL)
    
    stmt = (
        select(Map.id)
        .outerjoin(MapMember, (MapMember.map_id == Map.id) & (MapMember.user_id == user_id))
        .outerjoin(GroupMap, GroupMap.map_id == Map.id)
        .outerjoin(
            GroupMember, 
            (GroupMember.group_id == GroupMap.group_id) & (GroupMember.user_id == user_id)
        )
        .where(
            (Map.id == map_id) &
            (
                (Map.created_by == user_id) |
                (MapMember.id.is_not(None)) |
                (GroupMember.id.is_not(None))
            )
        )
        .limit(1)
    )
    
    result = await db.execute(stmt)
    return result.scalar_one_or_none() is not None
