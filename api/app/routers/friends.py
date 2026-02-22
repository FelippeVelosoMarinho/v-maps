from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from typing import List
from app.database import get_db
from app.models.user import User
from app.models.profile import Profile
from app.models.friendship import Friendship, FriendshipStatus
from app.schemas.friendship import (
    FriendshipCreate,
    FriendshipUpdate,
    FriendshipResponse,
    FriendResponse,
    UserSearchResult,
    FriendshipStatusEnum,
)
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/friends", tags=["Friends"])


@router.get("", response_model=List[FriendResponse])
async def get_friends(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retorna lista de amigos do usuário atual.
    """
    # Get accepted friendships where user is either requester or addressee
    result = await db.execute(
        select(Friendship)
        .where(
            and_(
                Friendship.status == FriendshipStatus.ACCEPTED,
                or_(
                    Friendship.requester_id == current_user.id,
                    Friendship.addressee_id == current_user.id
                )
            )
        )
    )
    friendships = result.scalars().all()
    
    friends = []
    for friendship in friendships:
        # Get the friend's user id
        friend_id = (
            friendship.addressee_id 
            if friendship.requester_id == current_user.id 
            else friendship.requester_id
        )
        
        # Get user and profile
        user_result = await db.execute(
            select(User).where(User.id == friend_id)
        )
        friend_user = user_result.scalar_one_or_none()
        
        if friend_user:
            profile_result = await db.execute(
                select(Profile).where(Profile.user_id == friend_id)
            )
            profile = profile_result.scalar_one_or_none()
            
            friends.append(FriendResponse(
                id=friend_user.id,
                email=friend_user.email,
                username=profile.username if profile else None,
                avatar_url=profile.avatar_url if profile else None,
                bio=profile.bio if profile else None,
                friendship_id=friendship.id,
                is_online=False  # TODO: Implement online status
            ))
    
    return friends


@router.get("/requests", response_model=List[FriendshipResponse])
async def get_friend_requests(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retorna solicitações de amizade pendentes recebidas.
    """
    result = await db.execute(
        select(Friendship)
        .where(
            and_(
                Friendship.addressee_id == current_user.id,
                Friendship.status == FriendshipStatus.PENDING
            )
        )
    )
    requests = result.scalars().all()
    
    response = []
    for req in requests:
        # Get requester info
        user_result = await db.execute(
            select(User).where(User.id == req.requester_id)
        )
        requester = user_result.scalar_one_or_none()
        
        profile_result = await db.execute(
            select(Profile).where(Profile.user_id == req.requester_id)
        )
        profile = profile_result.scalar_one_or_none()
        
        from app.schemas.friendship import FriendUser, FriendProfile
        
        friend_user = None
        if requester:
            friend_user = FriendUser(
                id=requester.id,
                email=requester.email,
                profile=FriendProfile(
                    id=profile.id if profile else "",
                    username=profile.username if profile else None,
                    avatar_url=profile.avatar_url if profile else None,
                    bio=profile.bio if profile else None
                ) if profile else None
            )
        
        response.append(FriendshipResponse(
            id=req.id,
            requester_id=req.requester_id,
            addressee_id=req.addressee_id,
            status=FriendshipStatusEnum(req.status.value),
            created_at=req.created_at,
            updated_at=req.updated_at,
            friend=friend_user
        ))
    
    return response


@router.get("/sent", response_model=List[FriendshipResponse])
async def get_sent_requests(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retorna solicitações de amizade enviadas pendentes.
    """
    result = await db.execute(
        select(Friendship)
        .where(
            and_(
                Friendship.requester_id == current_user.id,
                Friendship.status == FriendshipStatus.PENDING
            )
        )
    )
    return result.scalars().all()


@router.post("", response_model=FriendshipResponse)
async def send_friend_request(
    data: FriendshipCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Envia solicitação de amizade para outro usuário.
    """
    if data.addressee_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Você não pode adicionar a si mesmo como amigo"
        )
    
    # Check if addressee exists
    result = await db.execute(
        select(User).where(User.id == data.addressee_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    # Check if friendship already exists
    result = await db.execute(
        select(Friendship)
        .where(
            or_(
                and_(
                    Friendship.requester_id == current_user.id,
                    Friendship.addressee_id == data.addressee_id
                ),
                and_(
                    Friendship.requester_id == data.addressee_id,
                    Friendship.addressee_id == current_user.id
                )
            )
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        if existing.status == FriendshipStatus.ACCEPTED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Vocês já são amigos"
            )
        elif existing.status == FriendshipStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Já existe uma solicitação pendente"
            )
        elif existing.status == FriendshipStatus.REJECTED:
            # Allow re-sending if previously rejected
            existing.status = FriendshipStatus.PENDING
            existing.requester_id = current_user.id
            existing.addressee_id = data.addressee_id
            await db.commit()
            await db.refresh(existing)
            return existing
    
    friendship = Friendship(
        requester_id=current_user.id,
        addressee_id=data.addressee_id,
        status=FriendshipStatus.PENDING
    )
    
    db.add(friendship)
    await db.commit()
    await db.refresh(friendship)
    
    # Notify addressee
    await manager.broadcast([data.addressee_id], {
        "type": "friend_request",
        "title": "Nova Solicitação de Amizade",
        "content": f"{current_user.email} quer ser seu amigo.",
        "friendship_id": friendship.id,
        "requester_id": current_user.id
    })
    
    return friendship


@router.put("/{friendship_id}", response_model=FriendshipResponse)
async def respond_to_friend_request(
    friendship_id: str,
    data: FriendshipUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Aceita ou rejeita uma solicitação de amizade.
    """
    result = await db.execute(
        select(Friendship).where(Friendship.id == friendship_id)
    )
    friendship = result.scalar_one_or_none()
    
    if not friendship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Solicitação não encontrada"
        )
    
    # Only addressee can accept/reject
    if friendship.addressee_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para responder esta solicitação"
        )
    
    if friendship.status != FriendshipStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esta solicitação já foi respondida"
        )
    
    friendship.status = FriendshipStatus(data.status.value)
    await db.commit()
    await db.refresh(friendship)
    
    if friendship.status == FriendshipStatus.ACCEPTED:
        manager.invalidate_friend_cache(friendship.requester_id)
        manager.invalidate_friend_cache(friendship.addressee_id)
        await manager.broadcast([friendship.requester_id], {
            "type": "friend_request_accepted",
            "title": "Solicitação Aceita",
            "content": f"{current_user.email} aceitou seu pedido de amizade.",
            "friendship_id": friendship.id,
            "friend_id": current_user.id
        })

    return friendship


@router.delete("/{friendship_id}")
async def remove_friend(
    friendship_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Remove amizade ou cancela solicitação.
    """
    result = await db.execute(
        select(Friendship).where(Friendship.id == friendship_id)
    )
    friendship = result.scalar_one_or_none()
    
    if not friendship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Amizade não encontrada"
        )
    
    # Only participants can delete
    if current_user.id not in [friendship.requester_id, friendship.addressee_id]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para esta ação"
        )
    
    requester_id, addressee_id = friendship.requester_id, friendship.addressee_id
    await db.delete(friendship)
    await db.commit()
    manager.invalidate_friend_cache(requester_id)
    manager.invalidate_friend_cache(addressee_id)

    return {"message": "Amizade removida com sucesso"}


@router.get("/search", response_model=List[UserSearchResult])
async def search_users(
    q: str = Query(..., min_length=2, description="Termo de busca"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Busca usuários por email ou username.
    """
    search_term = f"%{q.lower()}%"
    
    # Search users by email or username
    result = await db.execute(
        select(User, Profile)
        .outerjoin(Profile, User.id == Profile.user_id)
        .where(
            and_(
                User.id != current_user.id,
                User.is_active == True,
                or_(
                    User.email.ilike(search_term),
                    Profile.username.ilike(search_term)
                )
            )
        )
        .limit(20)
    )
    users = result.all()
    
    # Get friendship status for each user
    results = []
    for user, profile in users:
        # Check if there's an existing friendship
        friendship_result = await db.execute(
            select(Friendship)
            .where(
                or_(
                    and_(
                        Friendship.requester_id == current_user.id,
                        Friendship.addressee_id == user.id
                    ),
                    and_(
                        Friendship.requester_id == user.id,
                        Friendship.addressee_id == current_user.id
                    )
                )
            )
        )
        friendship = friendship_result.scalar_one_or_none()
        
        results.append(UserSearchResult(
            id=user.id,
            email=user.email,
            username=profile.username if profile else None,
            avatar_url=profile.avatar_url if profile else None,
            is_friend=friendship.status == FriendshipStatus.ACCEPTED if friendship else False,
            friendship_status=FriendshipStatusEnum(friendship.status.value) if friendship else None,
            friendship_id=friendship.id if friendship else None
        ))
    
    return results
