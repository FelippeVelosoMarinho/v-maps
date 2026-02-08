"""
Router para funcionalidades sociais: Likes, Comments, Perfil Público
"""
from fastapi import APIRouter, Depends, HTTPException, status, Body, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone
import json
import traceback
import logging
from app.database import get_db
from app.models.user import User
from app.models.profile import Profile
from app.models.map import Map
from app.models.place import Place
from app.models.check_in import CheckIn
from app.models.social import SocialPost, SocialPostLike, SocialPostComment
from app.models.friendship import Friendship, FriendshipStatus
from app.models.trip import Trip
from app.schemas.social import (
    PublicMapResponse, PublicProfileResponse, PublicCheckInResponse,
    SocialFeedResponse, SocialPostResponse, TripBookResponse
)
from app.schemas.check_in import CheckInWithDetails
from app.utils.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/social", tags=["Social"])

# =====================
# Helpers for Social Feed
# =====================

async def get_social_content_details(db: AsyncSession, post_type: str, content_id: str):
    content_item = None
    if post_type == 'check_in':
        res = await db.execute(select(CheckIn).where(CheckIn.id == content_id))
        ci = res.scalar_one_or_none()
        if ci:
             p_res = await db.execute(select(Profile).where(Profile.user_id == ci.user_id))
             profile = p_res.scalar_one_or_none()
             pl_res = await db.execute(select(Place).where(Place.id == ci.place_id))
             place = pl_res.scalar_one_or_none()
             
             content_item = CheckInWithDetails(
                id=ci.id,
                place_id=ci.place_id,
                user_id=ci.user_id,
                comment=ci.comment,
                rating=ci.rating,
                photo_url=ci.photo_url,
                visited_at=ci.visited_at,
                created_at=ci.created_at,
                profile=profile,
                place_name=place.name if place else "Local desconhecido",
                map_id=place.map_id if place else None,
                likes_count=0, 
                comments_count=0,
                is_liked=False,
                shared_to_feed=ci.shared_to_feed
            )
    elif post_type == 'trip':
         res = await db.execute(
             select(Trip)
             .where(Trip.id == content_id)
             .options(selectinload(Trip.participants), selectinload(Trip.locations))
         )
         trip = res.scalar_one_or_none()
         if trip:
             cr_res = await db.execute(select(Profile).where(Profile.user_id == trip.created_by))
             creator = cr_res.scalar_one_or_none()
             
             all_locs = sorted(trip.locations, key=lambda l: l.recorded_at)
             step = max(1, len(all_locs) // 20)
             sampled_locs = [{"lat": l.latitude, "lng": l.longitude} for l in all_locs[::step]]
             
             favorite_photos = []
             try:
                if trip.favorite_photos:
                    if isinstance(trip.favorite_photos, str):
                        favorite_photos = json.loads(trip.favorite_photos)
                    elif isinstance(trip.favorite_photos, list):
                        favorite_photos = trip.favorite_photos
             except: pass

             content_item = TripBookResponse(
                id=trip.id,
                name=trip.name,
                description=trip.description,
                map_id=trip.map_id,
                created_by=trip.created_by,
                started_at=trip.started_at,
                ended_at=trip.ended_at,
                participants_count=len(trip.participants),
                locations=sampled_locs,
                rating=trip.rating,
                favorite_photos=favorite_photos,
                creator_username=creator.username if creator else None,
                creator_avatar_url=creator.avatar_url if creator else None
             )
    elif post_type == 'map':
         res = await db.execute(select(Map).where(Map.id == content_id))
         map_obj = res.scalar_one_or_none()
         if map_obj:
             count_res = await db.execute(select(func.count(Place.id)).where(Place.map_id == map_obj.id))
             loc_count = count_res.scalar() or 0
             content_item = PublicMapResponse(
                id=map_obj.id,
                name=map_obj.name,
                icon=map_obj.icon,
                color=map_obj.color,
                location_count=loc_count,
                created_at=map_obj.created_at
             )
             
    return content_item


async def build_social_post_response(db: AsyncSession, post: SocialPost, current_user_id: str):
    # Get Post Author Profile
    p_res = await db.execute(select(Profile).where(Profile.user_id == post.user_id))
    author_profile = p_res.scalar_one_or_none()
    
    # Get Interactions
    likes_res = await db.execute(select(func.count(SocialPostLike.id)).where(SocialPostLike.post_id == post.id))
    likes_count = likes_res.scalar() or 0
    
    comments_res = await db.execute(select(func.count(SocialPostComment.id)).where(SocialPostComment.post_id == post.id))
    comments_count = comments_res.scalar() or 0
    
    is_liked_res = await db.execute(
        select(SocialPostLike)
        .where(and_(SocialPostLike.post_id == post.id, SocialPostLike.user_id == current_user_id))
    )
    is_liked = is_liked_res.scalar_one_or_none() is not None
    
    # Get Content
    content = await get_social_content_details(db, post.content_type, post.content_id)
    
    return SocialPostResponse(
        id=post.id,
        user_id=post.user_id,
        username=author_profile.username if author_profile else "Usuário",
        avatar_url=author_profile.avatar_url if author_profile else None,
        content_type=post.content_type,
        content_id=post.content_id,
        caption=post.caption,
        created_at=post.created_at,
        content=content,
        likes_count=likes_count,
        comments_count=comments_count,
        is_liked=is_liked
    )

# =====================
# Endpoints
# =====================

@router.get("/feed", response_model=SocialFeedResponse)
async def get_social_feed(
    limit: int = 50,
    skip: int = 0,
    feed_type: str = "for_you", # "for_you", "following", or "personal"
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obter feed social consolidado"""
    try:
        if limit <= 0:
            return SocialFeedResponse(items=[])
        
        if limit > 100:
            limit = 100
            
        query = select(SocialPost).join(User).outerjoin(Profile, Profile.user_id == SocialPost.user_id)
        
        if feed_type == "following":
            # Get friends
            friends_res = await db.execute(
                select(Friendship).where(
                    and_(Friendship.status == FriendshipStatus.ACCEPTED,
                         or_(Friendship.requester_id == current_user.id, Friendship.addressee_id == current_user.id))
                )
            )
            friend_ids = []
            for f in friends_res.scalars().all():
                 friend_ids.append(f.addressee_id if f.requester_id == current_user.id else f.requester_id)
            friend_ids.append(current_user.id) # Include self
            
            query = query.where(SocialPost.user_id.in_(friend_ids))
            
        elif feed_type == "personal":
            query = query.where(SocialPost.user_id == current_user.id)
            
        query = query.order_by(desc(SocialPost.created_at)).offset(skip).limit(limit)
        
        result = await db.execute(query)
        posts = result.scalars().all()
        
        feed_items = []
        for post in posts:
            resp = await build_social_post_response(db, post, current_user.id)
            # SÓ incluimos se o conteúdo ainda existir
            if resp.content:
                feed_items.append(resp)
                
        return SocialFeedResponse(items=feed_items)
    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"FATAL ERROR IN SOCIAL FEED: {str(e)}\n{error_trace}")
        raise HTTPException(
            status_code=500,
            detail=f"DEBUG ERROR: {str(e)} | Trace: {error_trace[:200]}..."
        )

@router.post("/posts/{post_id}/like")
async def like_post(
    post_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Curtir uma publicação do feed"""
    # Verificar se já curtiu
    existing = await db.execute(
        select(SocialPostLike).where(
            and_(SocialPostLike.post_id == post_id, SocialPostLike.user_id == current_user.id)
        )
    )
    if existing.scalar_one_or_none():
        return {"status": "already_liked"}
    
    new_like = SocialPostLike(post_id=post_id, user_id=current_user.id)
    db.add(new_like)
    await db.commit()
    return {"status": "liked"}

@router.delete("/posts/{post_id}/like")
async def unlike_post(
    post_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Descurtir uma publicação do feed"""
    existing = await db.execute(
        select(SocialPostLike).where(
            and_(SocialPostLike.post_id == post_id, SocialPostLike.user_id == current_user.id)
        )
    )
    like = existing.scalar_one_or_none()
    if like:
        await db.delete(like)
        await db.commit()
    return {"status": "unliked"}

@router.post("/posts/{post_id}/comments")
async def comment_post(
    post_id: str,
    content: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Comentar em uma publicação do feed"""
    new_comment = SocialPostComment(
        post_id=post_id,
        user_id=current_user.id,
        content=content
    )
    db.add(new_comment)
    await db.commit()
    return {"status": "commented"}

@router.get("/friends/suggestions", response_model=list[PublicProfileResponse])
async def get_friend_suggestions(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Sugestões de amigos"""
    # 1. Get my friends
    my_friends_res = await db.execute(
        select(Friendship).where(
            and_(Friendship.status == FriendshipStatus.ACCEPTED,
                 or_(Friendship.requester_id == current_user.id, Friendship.addressee_id == current_user.id))
        )
    )
    my_friend_ids = set()
    for f in my_friends_res.scalars().all():
        my_friend_ids.add(f.addressee_id if f.requester_id == current_user.id else f.requester_id)
        
    if not my_friend_ids:
        # Fallback: Random users
        random_users = await db.execute(
            select(Profile).where(Profile.user_id != current_user.id).limit(limit)
        )
        profiles = random_users.scalars().all()
    else:
        # 2. Get friends of friends
        fof_res = await db.execute(
            select(Friendship)
            .where(
                and_(
                    Friendship.status == FriendshipStatus.ACCEPTED,
                    or_(Friendship.requester_id.in_(my_friend_ids), Friendship.addressee_id.in_(my_friend_ids))
                )
            )
        )
        fof_ids = set()
        for f in fof_res.scalars().all():
            fid = f.addressee_id if f.requester_id in my_friend_ids else f.requester_id
            if fid != current_user.id and fid not in my_friend_ids:
                fof_ids.add(fid)
        
        if not fof_ids:
            # Fallback
            random_res = await db.execute(
                select(Profile).where(
                    and_(Profile.user_id != current_user.id, ~Profile.user_id.in_(my_friend_ids))
                ).limit(limit)
            )
            profiles = random_res.scalars().all()
        else:
            profile_res = await db.execute(
                select(Profile).where(Profile.user_id.in_(list(fof_ids))).limit(limit)
            )
            profiles = profile_res.scalars().all()

    # Format output
    result = []
    for p in profiles:
        # Get stats
        map_count = await db.execute(select(func.count(Map.id)).where(Map.created_by == p.user_id))
        checkin_count = await db.execute(select(func.count(CheckIn.id)).where(CheckIn.user_id == p.user_id))
        friend_count = await db.execute(select(func.count(Friendship.id)).where(
            and_(Friendship.status == FriendshipStatus.ACCEPTED, 
                 or_(Friendship.requester_id == p.user_id, Friendship.addressee_id == p.user_id))
        ))
        
        result.append(PublicProfileResponse(
            id=p.id,
            user_id=p.user_id,
            username=p.username,
            avatar_url=p.avatar_url,
            bio=p.bio,
            created_at=p.created_at,
            map_count=map_count.scalar() or 0,
            check_in_count=checkin_count.scalar() or 0,
            friend_count=friend_count.scalar() or 0
        ))
    return result

@router.get("/profile/{user_id}", response_model=PublicProfileResponse)
async def get_public_profile(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Busca o perfil público de um usuário"""
    res = await db.execute(select(Profile).where(Profile.user_id == user_id))
    profile = res.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Perfil não encontrado")
    
    # Check friendship
    f_res = await db.execute(
        select(Friendship).where(
            or_(
                and_(Friendship.requester_id == current_user.id, Friendship.addressee_id == user_id),
                and_(Friendship.requester_id == user_id, Friendship.addressee_id == current_user.id)
            )
        )
    )
    friendship = f_res.scalar_one_or_none()
    
    is_friend = friendship and friendship.status == FriendshipStatus.ACCEPTED
    status_str = friendship.status.value if friendship else None

    # Stats
    map_count = await db.execute(select(func.count(Map.id)).where(Map.created_by == user_id))
    checkin_count = await db.execute(select(func.count(CheckIn.id)).where(CheckIn.user_id == user_id))
    friend_count = await db.execute(select(func.count(Friendship.id)).where(
        and_(Friendship.status == FriendshipStatus.ACCEPTED, 
             or_(Friendship.requester_id == user_id, Friendship.addressee_id == user_id))
    ))
    
    # Public maps
    map_res = await db.execute(select(Map).where(Map.created_by == user_id).limit(20))
    maps = map_res.scalars().all()
    public_maps = []
    for m in maps:
        loc_res = await db.execute(select(func.count(Place.id)).where(Place.map_id == m.id))
        public_maps.append(PublicMapResponse(
            id=m.id, name=m.name, icon=m.icon, color=m.color,
            location_count=loc_res.scalar() or 0, created_at=m.created_at
        ))

    return PublicProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        username=profile.username,
        avatar_url=profile.avatar_url,
        bio=profile.bio,
        created_at=profile.created_at,
        map_count=map_count.scalar() or 0,
        check_in_count=checkin_count.scalar() or 0,
        friend_count=friend_count.scalar() or 0,
        is_friend=is_friend,
        friendship_status=status_str,
        public_maps=public_maps
    )
