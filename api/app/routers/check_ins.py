from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, timezone
import os
import uuid
import aiofiles
from app.database import get_db
from app.models.user import User
from app.models.place import Place
from app.models.check_in import CheckIn
from app.models.profile import Profile
from app.models.social import CheckInLike, CheckInComment
from app.schemas.check_in import CheckInCreate, CheckInResponse, CheckInWithDetails
from app.utils.dependencies import get_current_user
from app.utils.permissions import check_map_access
from app.models.map import Map # Import Map for queries

router = APIRouter(prefix="/check-ins", tags=["Check-ins"])


@router.get("", response_model=list[CheckInWithDetails])
async def get_check_ins(
    map_id: str | None = None,
    place_id: str | None = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retorna check-ins. Pode filtrar por map_id ou place_id.
    """
    query = select(CheckIn).order_by(CheckIn.visited_at.desc()).limit(limit)
    
    if place_id:
        # Verify place exists and user has access
        result = await db.execute(select(Place).where(Place.id == place_id))
        place = result.scalar_one_or_none()
        
        if not place:
            raise HTTPException(status_code=404, detail="Lugar não encontrado")
            
        if not await check_map_access(db, place.map_id, current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado ao mapa"
            )

        # Filtrar por place_id específico
        query = (
            select(CheckIn)
            .where(CheckIn.place_id == place_id)
            .order_by(CheckIn.visited_at.desc())
            .limit(limit)
        )
    elif map_id:
        # Check access to the map
        if not await check_map_access(db, map_id, current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado ao mapa"
            )
            
        # Filtrar por map_id (todos os check-ins de lugares nesse mapa)
        query = (
            select(CheckIn)
            .join(Place, Place.id == CheckIn.place_id)
            .where(Place.map_id == map_id)
            .order_by(CheckIn.visited_at.desc())
            .limit(limit)
        )
    
    result = await db.execute(query)
    check_ins = result.scalars().all()
    
    # Carregar detalhes adicionais
    check_ins_with_details = []
    for ci in check_ins:
        # Buscar perfil
        result = await db.execute(
            select(Profile).where(Profile.user_id == ci.user_id)
        )
        profile = result.scalar_one_or_none()
        
        # Buscar lugar
        result = await db.execute(
            select(Place).where(Place.id == ci.place_id)
        )
        place = result.scalar_one_or_none()
        
        # Contar likes
        likes_result = await db.execute(
            select(func.count(CheckInLike.id)).where(CheckInLike.check_in_id == ci.id)
        )
        likes_count = likes_result.scalar() or 0
        
        # Contar comments
        comments_result = await db.execute(
            select(func.count(CheckInComment.id)).where(CheckInComment.check_in_id == ci.id)
        )
        comments_count = comments_result.scalar() or 0
        
        # Verificar se o usuário atual curtiu
        is_liked_result = await db.execute(
            select(CheckInLike).where(
                and_(
                    CheckInLike.check_in_id == ci.id,
                    CheckInLike.user_id == current_user.id
                )
            )
        )
        is_liked = is_liked_result.scalar_one_or_none() is not None
        
        check_ins_with_details.append(CheckInWithDetails(
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
    
    return check_ins_with_details


@router.post("", response_model=CheckInWithDetails, status_code=status.HTTP_201_CREATED)
async def create_check_in(
    place_id: str = Form(...),
    comment: str | None = Form(None),
    rating: int | None = Form(None),
    photo: UploadFile | None = File(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Cria um novo check-in com upload opcional de foto e avaliação.
    """
    # Validar rating
    if rating is not None and (rating < 1 or rating > 5):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rating deve ser entre 1 e 5"
        )
    
    # Verificar se o lugar existe
    result = await db.execute(select(Place).where(Place.id == place_id))
    place = result.scalar_one_or_none()
    
    if not place:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lugar não encontrado"
        )
        
    # Check access to the map
    if not await check_map_access(db, place.map_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem acesso a este mapa"
        )
    
    photo_url = None
    
    # Processar upload de foto
    if photo:
        # Validar tamanho
        contents = await photo.read()
        if len(contents) > settings.max_file_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Arquivo muito grande. Máximo: 5MB"
            )
        
        # Validar tipo
        allowed_types = ["image/jpeg", "image/png", "image/webp"]
        if photo.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tipo de arquivo não permitido"
            )
        
        # Salvar arquivo
        os.makedirs(settings.upload_dir, exist_ok=True)
        file_ext = photo.filename.split(".")[-1] if photo.filename else "jpg"
        file_name = f"{current_user.id}/{uuid.uuid4()}.{file_ext}"
        file_path = os.path.join(settings.upload_dir, file_name)
        
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(contents)
        
        photo_url = f"/uploads/{file_name}"
    
    new_check_in = CheckIn(
        place_id=place_id,
        user_id=current_user.id,
        comment=comment,
        rating=rating,
        photo_url=photo_url,
        visited_at=datetime.now(timezone.utc)
    )
    db.add(new_check_in)
    await db.commit()
    await db.refresh(new_check_in)
    
    # Buscar perfil do usuário
    result = await db.execute(
        select(Profile).where(Profile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()

    # Notify friends
    from app.utils.websockets import manager
    await manager.broadcast_to_friends(current_user.id, {
        "type": "new_post",
        "content_type": "check_in",
        "id": new_check_in.id,
        "title": "Novo Check-in",
        "description": f"{current_user.email} fez check-in em {place.name}",
        "created_by": current_user.id,
        "place_id": place.id,
        "map_id": place.map_id
    }, db)
    
    # Retornar com detalhes completos
    return CheckInWithDetails(
        id=new_check_in.id,
        place_id=new_check_in.place_id,
        user_id=new_check_in.user_id,
        comment=new_check_in.comment,
        rating=new_check_in.rating,
        photo_url=new_check_in.photo_url,
        visited_at=new_check_in.visited_at,
        created_at=new_check_in.created_at,
        profile=profile,
        place_name=place.name,
        map_id=place.map_id
    )


@router.delete("/{check_in_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_check_in(
    check_in_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Exclui um check-in.
    """
    result = await db.execute(select(CheckIn).where(CheckIn.id == check_in_id))
    check_in = result.scalar_one_or_none()
    
    if not check_in:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Check-in não encontrado"
        )
    
    if check_in.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas o autor pode excluir o check-in"
        )
    
    # Remover foto se existir
    if check_in.photo_url:
        file_path = os.path.join(settings.upload_dir, check_in.photo_url.replace("/uploads/", ""))
        if os.path.exists(file_path):
            os.remove(file_path)
    
    await db.delete(check_in)
    await db.commit()
