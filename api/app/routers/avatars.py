from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Avatar, User
from app.schemas.avatar import (
    AvatarCreate,
    AvatarUpdate,
    AvatarResponse,
    AVATAR_OPTIONS
)
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/avatars", tags=["avatars"])


@router.get("/options")
async def get_avatar_options():
    """Obter todas as opções disponíveis para customização de avatar"""
    return AVATAR_OPTIONS


@router.get("/me", response_model=AvatarResponse)
async def get_my_avatar(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Obter o avatar do usuário atual"""
    result = await db.execute(
        select(Avatar).where(Avatar.user_id == current_user.id)
    )
    avatar = result.scalars().first()
    
    if not avatar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Avatar não encontrado. Crie um avatar primeiro."
        )
    
    return avatar


@router.get("/{user_id}", response_model=AvatarResponse)
async def get_user_avatar(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Obter o avatar de um usuário específico (público)"""
    result = await db.execute(
        select(Avatar).where(Avatar.user_id == user_id)
    )
    avatar = result.scalars().first()
    
    if not avatar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Avatar não encontrado"
        )
    
    return avatar


@router.post("", response_model=AvatarResponse, status_code=status.HTTP_201_CREATED)
async def create_avatar(
    avatar_data: AvatarCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Criar avatar para o usuário atual"""
    # Verificar se já existe avatar
    result = await db.execute(
        select(Avatar).where(Avatar.user_id == current_user.id)
    )
    existing_avatar = result.scalars().first()
    
    if existing_avatar:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Você já possui um avatar. Use o endpoint de atualização."
        )
    
    # Criar novo avatar
    avatar = Avatar(
        user_id=current_user.id,
        **avatar_data.model_dump()
    )
    
    db.add(avatar)
    await db.commit()
    await db.refresh(avatar)
    
    return avatar


@router.put("", response_model=AvatarResponse)
async def update_avatar(
    avatar_data: AvatarUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Atualizar avatar do usuário atual"""
    result = await db.execute(
        select(Avatar).where(Avatar.user_id == current_user.id)
    )
    avatar = result.scalars().first()
    
    if not avatar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Avatar não encontrado. Crie um avatar primeiro."
        )
    
    # Atualizar apenas campos fornecidos
    update_data = avatar_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(avatar, field, value)
    
    await db.commit()
    await db.refresh(avatar)
    
    return avatar


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_avatar(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Deletar avatar do usuário atual"""
    result = await db.execute(
        select(Avatar).where(Avatar.user_id == current_user.id)
    )
    avatar = result.scalars().first()
    
    if not avatar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Avatar não encontrado"
        )
    
    await db.delete(avatar)
    await db.commit()
    
    return None
