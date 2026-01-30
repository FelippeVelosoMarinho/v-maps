"""
Router para funcionalidades sociais: Likes, Comments, Perfil Público
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone
from app.database import get_db
from app.models.user import User
from app.models.profile import Profile
from app.models.map import Map
from app.models.place import Place
from app.models.check_in import CheckIn
from app.models.social import CheckInLike, CheckInComment, TripLike, TripComment, MapLike, MapComment
from app.models.friendship import Friendship, FriendshipStatus
from app.models.map_member import MapMember
from app.models.group import GroupMember, GroupMap
from app.models.user_social import FavoritePlace, WishListPlace
from app.models.trip import Trip, TripParticipant, TripLocation
from app.schemas.check_in import CheckInWithDetails
from app.schemas.social import (
    CheckInLikeResponse,
    CheckInCommentCreate,
    CheckInCommentUpdate,
    CheckInCommentResponse,
    PublicProfileResponse,
    PublicMapResponse,
    PublicCheckInResponse,
    MapMemberWithColor,
    PlaceWithCreator,
    UserPlaceInteractionCreate,
    UserPlaceInteractionResponse,
    TripBookResponse,
    SocialFeedResponse,
)
from app.utils.dependencies import get_current_user
from app.utils.permissions import check_map_access
import json

router = APIRouter(prefix="/social", tags=["Social"])


# =====================
# Likes
# =====================

@router.post("/check-ins/{check_in_id}/like", response_model=CheckInLikeResponse)
async def like_check_in(
    check_in_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Curtir um check-in"""
    # Verificar se o check-in existe
    result = await db.execute(
        select(CheckIn).where(CheckIn.id == check_in_id)
    )
    check_in = result.scalar_one_or_none()
    
    if not check_in:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Check-in não encontrado"
        )
    
    # Verificar se já curtiu
    result = await db.execute(
        select(CheckInLike).where(
            and_(
                CheckInLike.check_in_id == check_in_id,
                CheckInLike.user_id == current_user.id
            )
        )
    )
    existing_like = result.scalar_one_or_none()
    
    if existing_like:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Você já curtiu este check-in"
        )
    
    # Criar like
    like = CheckInLike(
        check_in_id=check_in_id,
        user_id=current_user.id
    )
    db.add(like)
    await db.commit()
    await db.refresh(like)
    
    # Buscar dados do perfil
    result = await db.execute(
        select(Profile).where(Profile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    
    return CheckInLikeResponse(
        id=like.id,
        check_in_id=like.check_in_id,
        user_id=like.user_id,
        username=profile.username if profile else None,
        avatar_url=profile.avatar_url if profile else None,
        created_at=like.created_at
    )


@router.delete("/check-ins/{check_in_id}/like", status_code=status.HTTP_204_NO_CONTENT)
async def unlike_check_in(
    check_in_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remover curtida de um check-in"""
    result = await db.execute(
        select(CheckInLike).where(
            and_(
                CheckInLike.check_in_id == check_in_id,
                CheckInLike.user_id == current_user.id
            )
        )
    )
    like = result.scalar_one_or_none()
    
    if not like:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Like não encontrado"
        )
    
    await db.delete(like)
    await db.commit()


@router.get("/check-ins/{check_in_id}/likes", response_model=list[CheckInLikeResponse])
async def get_check_in_likes(
    check_in_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Listar curtidas de um check-in"""
    result = await db.execute(
        select(CheckInLike, Profile)
        .outerjoin(Profile, Profile.user_id == CheckInLike.user_id)
        .where(CheckInLike.check_in_id == check_in_id)
        .order_by(CheckInLike.created_at.desc())
    )
    
    likes = []
    for like, profile in result.all():
        likes.append(CheckInLikeResponse(
            id=like.id,
            check_in_id=like.check_in_id,
            user_id=like.user_id,
            username=profile.username if profile else None,
            avatar_url=profile.avatar_url if profile else None,
            created_at=like.created_at
        ))
    
    return likes


# =====================
# Comments
# =====================

@router.post("/check-ins/{check_in_id}/comments", response_model=CheckInCommentResponse)
async def create_comment(
    check_in_id: str,
    comment_data: CheckInCommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Criar comentário em um check-in"""
    # Verificar se o check-in existe
    result = await db.execute(
        select(CheckIn).where(CheckIn.id == check_in_id)
    )
    check_in = result.scalar_one_or_none()
    
    if not check_in:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Check-in não encontrado"
        )
    
    # Criar comentário
    comment = CheckInComment(
        check_in_id=check_in_id,
        user_id=current_user.id,
        content=comment_data.content
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    
    # Buscar dados do perfil
    result = await db.execute(
        select(Profile).where(Profile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    
    return CheckInCommentResponse(
        id=comment.id,
        check_in_id=comment.check_in_id,
        user_id=comment.user_id,
        username=profile.username if profile else None,
        avatar_url=profile.avatar_url if profile else None,
        content=comment.content,
        created_at=comment.created_at,
        updated_at=comment.updated_at
    )


@router.get("/check-ins/{check_in_id}/comments", response_model=list[CheckInCommentResponse])
async def get_check_in_comments(
    check_in_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Listar comentários de um check-in"""
    result = await db.execute(
        select(CheckInComment, Profile)
        .outerjoin(Profile, Profile.user_id == CheckInComment.user_id)
        .where(CheckInComment.check_in_id == check_in_id)
        .order_by(CheckInComment.created_at.asc())
    )
    
    comments = []
    for comment, profile in result.all():
        comments.append(CheckInCommentResponse(
            id=comment.id,
            check_in_id=comment.check_in_id,
            user_id=comment.user_id,
            username=profile.username if profile else None,
            avatar_url=profile.avatar_url if profile else None,
            content=comment.content,
            created_at=comment.created_at,
            updated_at=comment.updated_at
        ))
    
    return comments


@router.put("/comments/{comment_id}", response_model=CheckInCommentResponse)
async def update_comment(
    comment_id: str,
    comment_data: CheckInCommentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Atualizar comentário"""
    result = await db.execute(
        select(CheckInComment).where(CheckInComment.id == comment_id)
    )
    comment = result.scalar_one_or_none()
    
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comentário não encontrado"
        )
    
    if comment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não pode editar este comentário"
        )
    
    comment.content = comment_data.content
    await db.commit()
    await db.refresh(comment)
    
    # Buscar dados do perfil
    result = await db.execute(
        select(Profile).where(Profile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    
    return CheckInCommentResponse(
        id=comment.id,
        check_in_id=comment.check_in_id,
        user_id=comment.user_id,
        username=profile.username if profile else None,
        avatar_url=profile.avatar_url if profile else None,
        content=comment.content,
        created_at=comment.created_at,
        updated_at=comment.updated_at
    )


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Deletar comentário"""
    result = await db.execute(
        select(CheckInComment).where(CheckInComment.id == comment_id)
    )
    comment = result.scalar_one_or_none()
    
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comentário não encontrado"
        )
    
    if comment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não pode deletar este comentário"
        )
    
    await db.delete(comment)
    await db.commit()


# =====================
# Social Feed
# =====================

@router.get("/feed", response_model=SocialFeedResponse)
async def get_social_feed(
    limit: int = 50,
    skip: int = 0,
    feed_type: str = "for_you", # "for_you" (global), "following" (friends), or "personal" (me)
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obter feed social (check-ins, viagens e novos lugares) em ordem cronológica"""
    
    user_ids = []
    is_public_view = feed_type == "for_you"
    is_personal_view = feed_type == "personal"
    
    if is_public_view:
        # Explorar view: Show all public content + explicit shares
        pass
    elif is_personal_view:
        # Postar view: Show only MY items (shared or not)
        user_ids = [current_user.id]
    else:
        # Following view: Show only friends + self
        friends_result = await db.execute(
            select(Friendship).where(
                and_(
                    Friendship.status == FriendshipStatus.ACCEPTED,
                    or_(
                        Friendship.requester_id == current_user.id,
                        Friendship.addressee_id == current_user.id
                    )
                )
            )
        )
        friendships = friends_result.scalars().all()
        user_ids = [f.addressee_id if f.requester_id == current_user.id else f.requester_id for f in friendships]
        user_ids.append(current_user.id)
    
    items = []

    # 1. Buscar check-ins
    ci_query = select(CheckIn).join(Place).join(Map)
    if is_public_view:
        # No feed global, mostramos o que é de mapa público ou explicitamente compartilhado
        ci_query = ci_query.where(
            or_(
                Map.is_public == True, 
                Map.is_shared == True,
                CheckIn.shared_to_feed == True
            )
        )
    elif is_personal_view:
        ci_query = ci_query.where(CheckIn.user_id == current_user.id)
    else:
        # No feed de amigos, mostramos o que é dos amigos (mesmo que não seja público no global)
        # OU o que o usuário explicitamente compartilhou
        ci_query = ci_query.where(
            or_(
                CheckIn.user_id.in_(user_ids),
                CheckIn.shared_to_feed == True
            )
        )
        
    ci_query = ci_query.order_by(CheckIn.visited_at.desc()).limit(limit + skip)
    result = await db.execute(ci_query)
    check_ins = result.scalars().all()
    
    for ci in check_ins:
        p_result = await db.execute(select(Profile).where(Profile.user_id == ci.user_id))
        profile = p_result.scalar_one_or_none()
        
        pl_result = await db.execute(select(Place).where(Place.id == ci.place_id))
        place = pl_result.scalar_one_or_none()
        
        l_result = await db.execute(select(func.count(CheckInLike.id)).where(CheckInLike.check_in_id == ci.id))
        likes_count = l_result.scalar() or 0
        
        c_result = await db.execute(select(func.count(CheckInComment.id)).where(CheckInComment.check_in_id == ci.id))
        comments_count = c_result.scalar() or 0
        
        il_result = await db.execute(
            select(CheckInLike).where(
                and_(CheckInLike.check_in_id == ci.id, CheckInLike.user_id == current_user.id)
            )
        )
        is_liked = il_result.scalar_one_or_none() is not None
        
        items.append(CheckInWithDetails(
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
            likes_count=likes_count,
            comments_count=comments_count,
            is_liked=is_liked,
            shared_to_feed=ci.shared_to_feed
        ))

    # 2. Buscar viagens finalizadas
    t_query = select(Trip).join(Map).where(Trip.is_active == False)
    if is_public_view:
        t_query = t_query.where(
            or_(
                Map.is_public == True, 
                Map.is_shared == True,
                Trip.shared_to_feed == True
            )
        )
    elif is_personal_view:
        t_query = t_query.where(Trip.created_by == current_user.id)
    else:
        t_query = t_query.where(
            or_(
                Trip.created_by.in_(user_ids),
                Trip.shared_to_feed == True
            )
        )
        
    t_query = t_query.order_by(Trip.ended_at.desc()).limit(limit + skip).options(
        selectinload(Trip.participants), 
        selectinload(Trip.locations)
    )
    trips_result = await db.execute(t_query)
    trips = trips_result.scalars().all()
    
    for trip in trips:
        creator_profile_result = await db.execute(
            select(Profile).where(Profile.user_id == trip.created_by)
        )
        creator_profile = creator_profile_result.scalar_one_or_none()
        
        all_locs = sorted(trip.locations, key=lambda l: l.recorded_at)
        step = max(1, len(all_locs) // 20)
        sampled_locs = []
        for i in range(0, len(all_locs), step):
            l = all_locs[i]
            sampled_locs.append({"lat": l.latitude, "lng": l.longitude})
            
        try:
            favorite_photos = []
            if trip.favorite_photos:
                if isinstance(trip.favorite_photos, str):
                    favorite_photos = json.loads(trip.favorite_photos)
                elif isinstance(trip.favorite_photos, list):
                    favorite_photos = trip.favorite_photos
        except Exception:
            favorite_photos = []
            
        # Contar likes do trip
        t_likes_res = await db.execute(select(func.count(TripLike.id)).where(TripLike.trip_id == trip.id))
        t_likes_count = t_likes_res.scalar() or 0
        
        # Contar comments do trip
        t_comm_res = await db.execute(select(func.count(TripComment.id)).where(TripComment.trip_id == trip.id))
        t_comm_count = t_comm_res.scalar() or 0
        
        # Verificar se curtiu
        t_il_res = await db.execute(select(TripLike).where(and_(TripLike.trip_id == trip.id, TripLike.user_id == current_user.id)))
        t_is_liked = t_il_res.scalar_one_or_none() is not None

        items.append(TripBookResponse(
            id=trip.id,
            name=trip.name,
            description=trip.description,
            map_id=trip.map_id,
            created_by=trip.created_by,
            started_at=trip.started_at,
            ended_at=trip.ended_at or trip.started_at,
            participants_count=len(trip.participants),
            locations=sampled_locs,
            rating=trip.rating,
            favorite_photos=favorite_photos,
            creator_username=creator_profile.username if creator_profile else "Viajante",
            creator_avatar_url=creator_profile.avatar_url if creator_profile else None,
            shared_to_feed=trip.shared_to_feed,
            likes_count=t_likes_count,
            comments_count=t_comm_count,
            is_liked=t_is_liked
        ))

    # 3. Buscar mapas compartilhados
    m_query = select(Map, Profile).join(Profile, Profile.user_id == Map.created_by)
    if is_public_view:
        m_query = m_query.where(or_(Map.is_public == True, Map.shared_to_feed == True))
    elif is_personal_view:
        m_query = m_query.where(Map.created_by == current_user.id)
    else:
        m_query = m_query.where(or_(Map.created_by.in_(user_ids), Map.shared_to_feed == True))
        
    m_query = m_query.order_by(Map.created_at.desc()).limit(limit + skip)
    maps_result = await db.execute(m_query)
    
    for map_obj, profile in maps_result.all():
        # Contar lugares no mapa
        loc_count_result = await db.execute(select(func.count(Place.id)).where(Place.map_id == map_obj.id))
        loc_count = loc_count_result.scalar() or 0
        
        # Stats do Mapa
        m_likes_res = await db.execute(select(func.count(MapLike.id)).where(MapLike.map_id == map_obj.id))
        m_likes_count = m_likes_res.scalar() or 0
        
        m_comm_res = await db.execute(select(func.count(MapComment.id)).where(MapComment.map_id == map_obj.id))
        m_comm_count = m_comm_res.scalar() or 0
        
        m_il_res = await db.execute(select(MapLike).where(and_(MapLike.map_id == map_obj.id, MapLike.user_id == current_user.id)))
        m_is_liked = m_il_res.scalar_one_or_none() is not None

        items.append(PublicMapResponse(
            id=map_obj.id,
            name=map_obj.name,
            icon=map_obj.icon,
            color=map_obj.color,
            location_count=loc_count,
            created_at=map_obj.created_at,
            shared_to_feed=map_obj.shared_to_feed,
            likes_count=m_likes_count,
            comments_count=m_comm_count,
            is_liked=m_is_liked
        ))

    # 4. Buscar LUGARES (Tudo que existe no menu explorar) - Somente se não for pessoal
    if not is_personal_view:
        pl_query = select(Place, Profile).join(Map).outerjoin(Profile, Profile.user_id == Place.created_by)
        if is_public_view:
            pl_query = pl_query.where(or_(Map.is_public == True, Map.is_shared == True))
        else:
            pl_query = pl_query.where(Place.created_by.in_(user_ids))
            
        pl_query = pl_query.order_by(Place.created_at.desc()).limit(limit + skip)
        places_result = await db.execute(pl_query)
        
        for place, profile in places_result.all():
            items.append(PlaceWithCreator(
                id=place.id,
                map_id=place.map_id,
                name=place.name,
                description=place.description,
                lat=place.lat,
                lng=place.lng,
                address=place.address,
                google_place_id=place.google_place_id,
                created_by=place.created_by,
                creator_color=place.creator_color,
                creator_username=profile.username if profile else None,
                creator_avatar_url=profile.avatar_url if profile else None,
                created_at=place.created_at,
                updated_at=place.updated_at
            ))
        
    # Ordenar tudo pelo tempo
    def get_timestamp(item):
        ts = None
        if isinstance(item, CheckInWithDetails):
            ts = item.visited_at
        elif isinstance(item, TripBookResponse) or isinstance(item, PublicMapResponse):
            ts = item.created_at if isinstance(item, PublicMapResponse) else (item.ended_at or item.started_at)
        elif hasattr(item, 'created_at'):
            ts = item.created_at
            
        if ts is None:
            # Fallback very safe - assume UTC as it's the standard in the app
            from datetime import timezone
            return datetime.min.replace(tzinfo=timezone.utc)
        return ts
        
    items.sort(key=get_timestamp, reverse=True)
    
    return SocialFeedResponse(items=items[skip : skip + limit])


@router.post("/check-in/{check_in_id}/share")
async def share_check_in(
    check_in_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Compartilhar um check-in no feed social"""
    ci_result = await db.execute(select(CheckIn).where(CheckIn.id == check_in_id))
    check_in = ci_result.scalar_one_or_none()
    
    if not check_in:
        raise HTTPException(status_code=404, detail="Check-in não encontrado")
    
    if check_in.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    check_in.shared_to_feed = not check_in.shared_to_feed
    await db.commit()
    return {"status": "success", "shared": check_in.shared_to_feed}


@router.post("/trip/{trip_id}/share")
async def share_trip(
    trip_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Compartilhar uma viagem no feed social"""
    t_result = await db.execute(select(Trip).where(Trip.id == trip_id))
    trip = t_result.scalar_one_or_none()
    
    if not trip:
        raise HTTPException(status_code=404, detail="Viagem não encontrada")
    
    if trip.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    trip.shared_to_feed = not trip.shared_to_feed
    await db.commit()
    return {"status": "success", "shared": trip.shared_to_feed}


@router.post("/map/{map_id}/share")
async def share_map(
    map_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Compartilhar um mapa no feed social"""
    m_result = await db.execute(select(Map).where(Map.id == map_id))
    map_obj = m_result.scalar_one_or_none()
    
    if not map_obj:
        raise HTTPException(status_code=404, detail="Mapa não encontrado")
    
    if map_obj.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    map_obj.shared_to_feed = not map_obj.shared_to_feed
    await db.commit()
    return {"status": "success", "shared": map_obj.shared_to_feed}


@router.post("/map/{map_id}/copy")
async def copy_map(
    map_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Copiar um mapa compartilhado para a lista do usuário atual"""
    result = await db.execute(select(Map).where(Map.id == map_id))
    original_map = result.scalar_one_or_none()
    
    if not original_map:
        raise HTTPException(status_code=404, detail="Mapa não encontrado")
    
    # Criar novo mapa
    new_map = Map(
        name=f"Cópia de {original_map.name}",
        icon=original_map.icon,
        color=original_map.color,
        created_by=current_user.id,
        is_shared=False,
        is_public=False
    )
    db.add(new_map)
    await db.flush() # Gerar ID do novo mapa
    
    # Copiar lugares
    places_result = await db.execute(select(Place).where(Place.map_id == map_id))
    original_places = places_result.scalars().all()
    
    for place in original_places:
        new_place = Place(
            map_id=new_map.id,
            name=place.name,
            description=place.description,
            lat=place.lat,
            lng=place.lng,
            address=place.address,
            google_place_id=place.google_place_id,
            created_by=current_user.id,
            creator_color=place.creator_color
        )
        db.add(new_place)
        
    await db.commit()
    return {"status": "success", "new_map_id": new_map.id}


# =====================
# Favorites and Wishlist
# =====================

@router.post("/favorites", response_model=UserPlaceInteractionResponse)
async def add_favorite(
    data: UserPlaceInteractionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verificar se já é favorito
    existing = await db.execute(
        select(FavoritePlace).where(
            and_(FavoritePlace.user_id == current_user.id, FavoritePlace.place_id == data.place_id)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Lugar já está nos favoritos")
    
    fav = FavoritePlace(user_id=current_user.id, place_id=data.place_id)
    db.add(fav)
    await db.commit()
    await db.refresh(fav)
    return fav


@router.delete("/favorites/{place_id}", status_code=204)
async def remove_favorite(
    place_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(FavoritePlace).where(
            and_(FavoritePlace.user_id == current_user.id, FavoritePlace.place_id == place_id)
        )
    )
    fav = result.scalar_one_or_none()
    if not fav:
        raise HTTPException(status_code=404, detail="Não encontrado nos favoritos")
    await db.delete(fav)
    await db.commit()


@router.get("/favorites", response_model=list[PlaceWithCreator])
async def get_favorites(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obter lugares favoritos do usuário atual"""
    result = await db.execute(
        select(Place, Profile)
        .join(FavoritePlace, FavoritePlace.place_id == Place.id)
        .outerjoin(Profile, Profile.user_id == Place.created_by)
        .where(FavoritePlace.user_id == current_user.id)
        .order_by(FavoritePlace.created_at.desc())
    )
    
    places = []
    for place, profile in result.all():
        places.append(PlaceWithCreator(
            id=place.id,
            map_id=place.map_id,
            name=place.name,
            description=place.description,
            lat=place.lat,
            lng=place.lng,
            address=place.address,
            google_place_id=place.google_place_id,
            created_by=place.created_by,
            creator_color=place.creator_color,
            creator_username=profile.username if profile else None,
            creator_avatar_url=profile.avatar_url if profile else None,
            created_at=place.created_at,
            updated_at=place.updated_at
        ))
    
    return places


@router.post("/wishlist", response_model=UserPlaceInteractionResponse)
async def add_to_wishlist(
    data: UserPlaceInteractionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verificar se já está na lista
    existing = await db.execute(
        select(WishListPlace).where(
            and_(WishListPlace.user_id == current_user.id, WishListPlace.place_id == data.place_id)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Lugar já está na lista de desejos")
    
    wish = WishListPlace(user_id=current_user.id, place_id=data.place_id)
    db.add(wish)
    await db.commit()
    await db.refresh(wish)
    return wish


@router.delete("/wishlist/{place_id}", status_code=204)
async def remove_from_wishlist(
    place_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(WishListPlace).where(
            and_(WishListPlace.user_id == current_user.id, WishListPlace.place_id == place_id)
        )
    )
    wish = result.scalar_one_or_none()
    if not wish:
        raise HTTPException(status_code=404, detail="Não encontrado na lista de desejos")
    await db.delete(wish)
    await db.commit()


@router.get("/wishlist", response_model=list[PlaceWithCreator])
async def get_wishlist(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obter lugares na lista de desejos do usuário atual"""
    result = await db.execute(
        select(Place, Profile)
        .join(WishListPlace, WishListPlace.place_id == Place.id)
        .outerjoin(Profile, Profile.user_id == Place.created_by)
        .where(WishListPlace.user_id == current_user.id)
        .order_by(WishListPlace.created_at.desc())
    )
    
    places = []
    for place, profile in result.all():
        places.append(PlaceWithCreator(
            id=place.id,
            map_id=place.map_id,
            name=place.name,
            description=place.description,
            lat=place.lat,
            lng=place.lng,
            address=place.address,
            google_place_id=place.google_place_id,
            created_by=place.created_by,
            creator_color=place.creator_color,
            creator_username=profile.username if profile else None,
            creator_avatar_url=profile.avatar_url if profile else None,
            created_at=place.created_at,
            updated_at=place.updated_at
        ))
    
    return places


# =====================
# Public Profile
# =====================

@router.get("/profile/{user_id}", response_model=PublicProfileResponse)
async def get_public_profile(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obter perfil público de um usuário"""
    # Buscar perfil
    result = await db.execute(
        select(Profile).where(Profile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil não encontrado"
        )
    
    # Verificar se são amigos
    is_friend = False
    friendship_status = None
    
    result = await db.execute(
        select(Friendship).where(
            or_(
                and_(
                    Friendship.requester_id == current_user.id,
                    Friendship.addressee_id == user_id
                ),
                and_(
                    Friendship.requester_id == user_id,
                    Friendship.addressee_id == current_user.id
                )
            )
        )
    )
    friendship = result.scalar_one_or_none()
    
    if friendship:
        friendship_status = friendship.status.value
        is_friend = friendship.status == FriendshipStatus.ACCEPTED
    
    # Contar mapas públicos
    result = await db.execute(
        select(func.count(Map.id)).where(
            and_(
                Map.created_by == user_id,
                Map.is_public == True
            )
        )
    )
    map_count = result.scalar() or 0
    
    # Contar check-ins
    result = await db.execute(
        select(func.count(CheckIn.id)).where(CheckIn.user_id == user_id)
    )
    check_in_count = result.scalar() or 0
    
    # Contar amigos
    result = await db.execute(
        select(func.count(Friendship.id)).where(
            and_(
                or_(
                    Friendship.requester_id == user_id,
                    Friendship.addressee_id == user_id
                ),
                Friendship.status == FriendshipStatus.ACCEPTED
            )
        )
    )
    friend_count = result.scalar() or 0

    # Contar favoritos
    result = await db.execute(
        select(func.count(FavoritePlace.id)).where(FavoritePlace.user_id == user_id)
    )
    favorite_count = result.scalar() or 0

    # Contar wishlist
    result = await db.execute(
        select(func.count(WishListPlace.id)).where(WishListPlace.user_id == user_id)
    )
    wish_list_count = result.scalar() or 0
    
    # Buscar mapas públicos (ou todos se for amigo)
    public_maps = []
    if is_friend or current_user.id == user_id:
        result = await db.execute(
            select(Map, func.count(Place.id).label('location_count'))
            .outerjoin(Place, Place.map_id == Map.id)
            .where(
                and_(
                    Map.created_by == user_id,
                    or_(Map.is_public == True, is_friend)
                )
            )
            .group_by(Map.id)
            .order_by(Map.created_at.desc())
            .limit(10)
        )
        for map_obj, loc_count in result.all():
            public_maps.append(PublicMapResponse(
                id=map_obj.id,
                name=map_obj.name,
                icon=map_obj.icon,
                color=map_obj.color,
                location_count=loc_count,
                created_at=map_obj.created_at
            ))
    else:
        # Apenas mapas públicos
        result = await db.execute(
            select(Map, func.count(Place.id).label('location_count'))
            .outerjoin(Place, Place.map_id == Map.id)
            .where(
                and_(
                    Map.created_by == user_id,
                    Map.is_public == True
                )
            )
            .group_by(Map.id)
            .order_by(Map.created_at.desc())
            .limit(10)
        )
        for map_obj, loc_count in result.all():
            public_maps.append(PublicMapResponse(
                id=map_obj.id,
                name=map_obj.name,
                icon=map_obj.icon,
                color=map_obj.color,
                location_count=loc_count,
                created_at=map_obj.created_at
            ))
    
    # Buscar check-ins recentes (com likes e comments count)
    recent_check_ins = []
    result = await db.execute(
        select(
            CheckIn,
            Place.name.label('place_name'),
            func.count(func.distinct(CheckInLike.id)).label('like_count'),
            func.count(func.distinct(CheckInComment.id)).label('comment_count')
        )
        .join(Place, Place.id == CheckIn.place_id)
        .outerjoin(CheckInLike, CheckInLike.check_in_id == CheckIn.id)
        .outerjoin(CheckInComment, CheckInComment.check_in_id == CheckIn.id)
        .where(CheckIn.user_id == user_id)
        .group_by(CheckIn.id, Place.name)
        .order_by(CheckIn.created_at.desc())
        .limit(10)
    )
    
    for check_in, place_name, like_count, comment_count in result.all():
        recent_check_ins.append(PublicCheckInResponse(
            id=check_in.id,
            place_name=place_name,
            comment=check_in.comment,
            rating=check_in.rating,
            photo_url=check_in.photo_url,
            visited_at=check_in.visited_at,
            like_count=like_count,
            comment_count=comment_count
        ))
    
    return PublicProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        username=profile.username,
        avatar_url=profile.avatar_url,
        bio=profile.bio,
        created_at=profile.created_at,
        map_count=map_count,
        check_in_count=check_in_count,
        friend_count=friend_count,
        favorite_count=favorite_count,
        wish_list_count=wish_list_count,
        public_maps=public_maps,
        recent_check_ins=recent_check_ins,
        is_friend=is_friend,
        friendship_status=friendship_status
    )


# =====================
# Map Members with Colors
# =====================

# Cores disponíveis para membros
MEMBER_COLORS = [
    "blue", "red", "green", "purple", "orange", 
    "pink", "yellow", "cyan", "lime", "indigo"
]


@router.get("/maps/{map_id}/members", response_model=list[MapMemberWithColor])
async def get_map_members_with_colors(
    map_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obter membros do mapa com suas cores"""
    # Verificar acesso ao mapa
    result = await db.execute(
        select(Map).where(Map.id == map_id)
    )
    map_obj = result.scalar_one_or_none()
    
    if not map_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mapa não encontrado"
        )
    
    # Verificar se tem acesso via shared helper
    has_access = await check_map_access(db, map_id, current_user.id)
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem acesso a este mapa"
        )
    
    # Buscar membros diretos
    direct_result = await db.execute(
        select(MapMember, Profile)
        .outerjoin(Profile, Profile.user_id == MapMember.user_id)
        .where(MapMember.map_id == map_id)
    )
    
    # Buscar membros de grupos vinculados
    group_members_result = await db.execute(
        select(GroupMember, Profile)
        .join(GroupMap, GroupMap.group_id == GroupMember.group_id)
        .outerjoin(Profile, Profile.user_id == GroupMember.user_id)
        .where(GroupMap.map_id == map_id)
    )
    
    group_members_all = group_members_result.all()

    # Dicionário para evitar duplicatas: user_id -> MapMemberWithColor
    members_dict = {}
    
    # 1. Adicionar membros diretos (têm prioridade pois têm cor personalizada)
    for member, profile in direct_result.all():
        members_dict[member.user_id] = MapMemberWithColor(
            id=member.id,
            user_id=member.user_id,
            username=profile.username if profile else None,
            avatar_url=profile.avatar_url if profile else None,
            role=member.role,
            color=member.color,
            joined_at=member.joined_at
        )

    # 2. Adicionar owner (se não estiver)
    owner_result = await db.execute(select(Profile).where(Profile.user_id == map_obj.created_by))
    owner_profile = owner_result.scalar_one_or_none()
    
    if map_obj.created_by not in members_dict:
        members_dict[map_obj.created_by] = MapMemberWithColor(
            id=map_obj.id,
            user_id=map_obj.created_by,
            username=owner_profile.username if owner_profile else None,
            avatar_url=owner_profile.avatar_url if owner_profile else None,
            role="owner",
            color="#3B82F6",
            joined_at=map_obj.created_at
        )
        
    
    # 3. Adicionar membros de grupo (se ainda não estiverem)
    for member, profile in group_members_all:
        if member.user_id not in members_dict:
            # Gerar cor determinística baseada no user_id
            color_index = hash(member.user_id) % len(MEMBER_COLORS)
            assigned_color = MEMBER_COLORS[color_index]
            
            members_dict[member.user_id] = MapMemberWithColor(
                id=member.id, # ID do GroupMember
                user_id=member.user_id,
                username=profile.username if profile else None,
                avatar_url=profile.avatar_url if profile else None,
                role="group_member", # Role diferente para indicar origem
                color=assigned_color,
                joined_at=member.joined_at
            )
            
    return list(members_dict.values())


@router.put("/maps/{map_id}/members/{user_id}/color")
async def update_member_color(
    map_id: str,
    user_id: str,
    color: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Atualizar cor de um membro do mapa"""
    if color not in MEMBER_COLORS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cor inválida. Cores disponíveis: {', '.join(MEMBER_COLORS)}"
        )
    
    # Verificar se é owner do mapa
    result = await db.execute(
        select(Map).where(Map.id == map_id)
    )
    map_obj = result.scalar_one_or_none()
    
    if not map_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mapa não encontrado"
        )
    
    if map_obj.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas o dono do mapa pode alterar cores"
        )
    
    # Atualizar cor do membro
    result = await db.execute(
        select(MapMember).where(
            and_(
                MapMember.map_id == map_id,
                MapMember.user_id == user_id
            )
        )
    )
    member = result.scalar_one_or_none()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membro não encontrado"
        )
    
    member.color = color
    await db.commit()
    
    return {"message": "Cor atualizada com sucesso"}


# =====================
# Places with Creator Info
# =====================

@router.get("/maps/{map_id}/places", response_model=list[PlaceWithCreator])
async def get_map_places_with_creators(
    map_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obter lugares do mapa com informações do criador"""
    # Verificar acesso ao mapa
    result = await db.execute(
        select(Map).where(Map.id == map_id)
    )
    map_obj = result.scalar_one_or_none()
    
    if not map_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mapa não encontrado"
        )
    
    # Verificar se tem acesso (owner, membro ou group member)
    has_access = await check_map_access(db, map_id, current_user.id)
    
    if not has_access and not map_obj.is_public:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem acesso a este mapa"
        )
    
    # Buscar lugares com informações do criador
    result = await db.execute(
        select(Place, Profile)
        .outerjoin(Profile, Profile.user_id == Place.created_by)
        .where(Place.map_id == map_id)
        .order_by(Place.created_at)
    )
    
    places = []
    for place, profile in result.all():
        places.append(PlaceWithCreator(
            id=place.id,
            map_id=place.map_id,
            name=place.name,
            description=place.description,
            lat=place.lat,
            lng=place.lng,
            address=place.address,
            google_place_id=place.google_place_id,
            created_by=place.created_by,
            creator_color=place.creator_color,
            creator_username=profile.username if profile else None,
            creator_avatar_url=profile.avatar_url if profile else None,
            created_at=place.created_at,
            updated_at=place.updated_at
        ))
    
    return places
