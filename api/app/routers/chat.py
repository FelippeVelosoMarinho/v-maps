from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.models.map import Map
from app.models.chat_message import ChatMessage
from app.models.profile import Profile
from app.models.map_member import MapMember
from app.schemas.chat_message import ChatMessageCreate, ChatMessageResponse, ChatMessageWithProfile
from app.utils.dependencies import get_current_user

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
        .order_by(ChatMessage.created_at.asc())
        .limit(limit)
    )
    messages = result.scalars().all()
    
    # Carregar perfis
    messages_with_profiles = []
    for msg in messages:
        result = await db.execute(
            select(Profile).where(Profile.user_id == msg.user_id)
        )
        profile = result.scalar_one_or_none()
        
        messages_with_profiles.append(ChatMessageWithProfile(
            id=msg.id,
            map_id=msg.map_id,
            user_id=msg.user_id,
            content=msg.content,
            created_at=msg.created_at,
            profile=profile
        ))
    
    return messages_with_profiles


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
