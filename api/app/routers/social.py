"""
Router para funcionalidades sociais: Likes, Comments, Perfil Público
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models.user import User
from app.models.profile import Profile
from app.models.map import Map
from app.models.place import Place
from app.models.check_in import CheckIn
from app.models.social import CheckInLike, CheckInComment
from app.models.friendship import Friendship, FriendshipStatus
from app.models.map_member import MapMember
from app.models.group import GroupMember, GroupMap
from app.models.user_social import FavoritePlace, WishListPlace
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
)
from app.utils.dependencies import get_current_user
from app.utils.permissions import check_map_access

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

@router.get("/feed", response_model=list[CheckInWithDetails])
async def get_social_feed(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obter feed social (check-ins de amigos) em ordem cronológica"""
    # Buscar IDs dos amigos
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
    friend_ids = []
    for f in friendships:
        friend_ids.append(f.addressee_id if f.requester_id == current_user.id else f.requester_id)
    
    # Incluir o próprio usuário no feed
    user_ids = friend_ids + [current_user.id]
    
    # Buscar check-ins desses usuários
    result = await db.execute(
        select(CheckIn)
        .where(CheckIn.user_id.in_(user_ids))
        .order_by(CheckIn.visited_at.desc())
        .limit(limit)
    )
    check_ins = result.scalars().all()
    
    # Carregar detalhes (mesma lógica do router de check-ins)
    feed = []
    for ci in check_ins:
        # Perfil
        p_result = await db.execute(select(Profile).where(Profile.user_id == ci.user_id))
        profile = p_result.scalar_one_or_none()
        
        # Lugar
        pl_result = await db.execute(select(Place).where(Place.id == ci.place_id))
        place = pl_result.scalar_one_or_none()
        
        # Likes
        l_result = await db.execute(select(func.count(CheckInLike.id)).where(CheckInLike.check_in_id == ci.id))
        likes_count = l_result.scalar() or 0
        
        # Comments
        c_result = await db.execute(select(func.count(CheckInComment.id)).where(CheckInComment.check_in_id == ci.id))
        comments_count = c_result.scalar() or 0
        
        # Is Liked
        il_result = await db.execute(
            select(CheckInLike).where(
                and_(CheckInLike.check_in_id == ci.id, CheckInLike.user_id == current_user.id)
            )
        )
        is_liked = il_result.scalar_one_or_none() is not None
        
        feed.append(CheckInWithDetails(
            id=ci.id,
            place_id=ci.place_id,
            user_id=ci.user_id,
            comment=ci.comment,
            rating=ci.rating,
            photo_url=ci.photo_url,
            visited_at=ci.visited_at,
            created_at=ci.created_at,
            profile=profile,
            place_name=place.name if place else None,
            map_id=place.map_id if place else None,
            likes_count=likes_count,
            comments_count=comments_count,
            is_liked=is_liked
        ))
    
    return feed


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
