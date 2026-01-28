from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models.user import User
from app.models.map import Map
from app.models.chat_message import ChatMessage
from app.models.profile import Profile
from app.models.map import Map
from app.models.map_member import MapMember
from app.models.trip import Trip, TripParticipant
from app.schemas.chat_message import ChatMessageCreate, ChatMessageResponse, ChatMessageWithProfile
from app.utils.dependencies import get_current_user
from app.utils.websockets import manager

router = APIRouter(prefix="/chat", tags=["Chat"])


async def check_map_access(map_id: str, user_id: str, db: AsyncSession) -> Map:
    """Verifica se o usuário tem acesso ao mapa."""
    result = await db.execute(select(Map).where(Map.id == map_id))
    map_obj = result.scalar_one_or_none()
    
    if not map_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mapa não encontrado"
        )
    
    if map_obj.created_by != user_id:
        result = await db.execute(
            select(MapMember)
            .where(MapMember.map_id == map_id, MapMember.user_id == user_id)
        )
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado ao mapa"
            )
    
    return map_obj


async def check_trip_access(trip_id: str, user_id: str, db: AsyncSession) -> Trip:
    """Verifica se o usuário tem acesso à trip."""
    result = await db.execute(
        select(Trip)
        .where(Trip.id == trip_id)
        .options(selectinload(Trip.participants))
    )
    trip = result.scalar_one_or_none()
    
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Viagem não encontrada"
        )
    
    if not trip.is_active:
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esta viagem já foi encerrada"
        )

    is_participant = any(p.user_id == user_id and p.status == 'accepted' for p in trip.participants)
    if trip.created_by != user_id and not is_participant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado à viagem"
        )
    
    return trip


@router.get("/{map_id}/messages", response_model=list[ChatMessageWithProfile])
async def get_messages(
    map_id: str,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retorna mensagens de um mapa.
    """
    await check_map_access(map_id, current_user.id, db)
    
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.map_id == map_id)
        .options(selectinload(ChatMessage.user).selectinload(User.profile))
        .order_by(ChatMessage.created_at.asc())
        .limit(limit)
    )
    messages = result.scalars().all()
    
    # Return directly as the relationship is pre-loaded
    return [
        ChatMessageWithProfile(
            id=msg.id,
            map_id=msg.map_id,
            user_id=msg.user_id,
            content=msg.content,
            created_at=msg.created_at,
            profile=msg.user.profile if msg.user else None
        )
        for msg in messages
    ]


@router.post("/{map_id}/messages", response_model=ChatMessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    map_id: str,
    message_data: ChatMessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Envia uma mensagem no chat do mapa.
    """
    await check_map_access(map_id, current_user.id, db)
    
    new_message = ChatMessage(
        map_id=map_id,
        user_id=current_user.id,
        content=message_data.content
    )
    db.add(new_message)
    await db.commit()
    await db.refresh(new_message)
    
    # Broadcast to all map members (including owner)
    # Get map owner
    map_owner_id = (await db.execute(select(Map.created_by).where(Map.id == map_id))).scalar_one()
    
    # Get members
    members_result = await db.execute(select(MapMember.user_id).where(MapMember.map_id == map_id))
    member_ids = set(members_result.scalars().all())
    member_ids.add(map_owner_id)
    
    # Also fetch profile for broadcast
    profile_result = await db.execute(select(Profile).where(Profile.user_id == current_user.id))
    profile = profile_result.scalar_one_or_none()
    
    await manager.broadcast(list(member_ids), {
        "type": "chat_message",
        "map_id": map_id,
        "message": {
            "id": new_message.id,
            "user_id": new_message.user_id,
            "content": new_message.content,
            "created_at": new_message.created_at.isoformat(),
            "profile": {
                "username": profile.username if profile else None,
                "avatar_url": profile.avatar_url if profile else None
            } if profile else None
        }
    })
    
    return new_message


@router.delete("/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(
    message_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Exclui uma mensagem.
    """
    result = await db.execute(select(ChatMessage).where(ChatMessage.id == message_id))
    message = result.scalar_one_or_none()
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mensagem não encontrada"
        )
    
    if message.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas o autor pode excluir a mensagem"
        )
    
    await db.delete(message)
    await db.commit()


@router.get("/trip/{trip_id}/messages", response_model=list[ChatMessageWithProfile])
async def get_trip_messages(
    trip_id: str,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retorna mensagens de uma viagem.
    """
    await check_trip_access(trip_id, current_user.id, db)
    
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.trip_id == trip_id)
        .options(selectinload(ChatMessage.user).selectinload(User.profile))
        .order_by(ChatMessage.created_at.asc())
        .limit(limit)
    )
    messages = result.scalars().all()
    
    return [
        ChatMessageWithProfile(
            id=msg.id,
            trip_id=msg.trip_id,
            user_id=msg.user_id,
            content=msg.content,
            created_at=msg.created_at,
            profile=msg.user.profile if msg.user else None
        )
        for msg in messages
    ]


@router.post("/trip/{trip_id}/messages", response_model=ChatMessageResponse, status_code=status.HTTP_201_CREATED)
async def send_trip_message(
    trip_id: str,
    message_data: ChatMessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Envia uma mensagem no chat da viagem.
    """
    trip = await check_trip_access(trip_id, current_user.id, db)
    
    new_message = ChatMessage(
        trip_id=trip_id,
        user_id=current_user.id,
        content=message_data.content
    )
    db.add(new_message)
    await db.commit()
    await db.refresh(new_message)
    
    # Get all participants to broadcast
    participant_ids = [p.user_id for p in trip.participants if p.status == 'accepted']
    if trip.created_by not in participant_ids:
        participant_ids.append(trip.created_by)
    
    # Also fetch profile for broadcast
    profile_result = await db.execute(select(Profile).where(Profile.user_id == current_user.id))
    profile = profile_result.scalar_one_or_none()
    
    await manager.broadcast(list(participant_ids), {
        "type": "chat_message",
        "trip_id": trip_id,
        "message": {
            "id": new_message.id,
            "user_id": new_message.user_id,
            "content": new_message.content,
            "created_at": new_message.created_at.isoformat(),
            "profile": {
                "username": profile.username if profile else None,
                "avatar_url": profile.avatar_url if profile else None
            } if profile else None
        }
    })
    
    return new_message
