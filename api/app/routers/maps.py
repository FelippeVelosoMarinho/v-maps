from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.user import User
from app.models.map import Map
from app.models.place import Place
from app.models.map_member import MapMember
from app.schemas.map import MapCreate, MapUpdate, MapResponse
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/maps", tags=["Maps"])


@router.get("", response_model=list[MapResponse])
async def get_maps(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retorna todos os mapas do usuário (próprios + compartilhados).
    """
    # Mapas próprios
    result = await db.execute(
        select(Map).where(Map.created_by == current_user.id)
        .order_by(Map.created_at.desc())
    )
    own_maps = result.scalars().all()
    
    # Mapas onde é membro
    result = await db.execute(
        select(Map)
        .join(MapMember, MapMember.map_id == Map.id)
        .where(MapMember.user_id == current_user.id)
    )
    shared_maps = result.scalars().all()
    
    all_maps = list(own_maps) + [m for m in shared_maps if m.id not in [o.id for o in own_maps]]
    
    # Contar lugares por mapa
    maps_with_count = []
    for map_obj in all_maps:
        result = await db.execute(
            select(func.count()).select_from(Place).where(Place.map_id == map_obj.id)
        )
        count = result.scalar()
        map_dict = {
            "id": map_obj.id,
            "name": map_obj.name,
            "icon": map_obj.icon,
            "color": map_obj.color,
            "is_shared": map_obj.is_shared,
            "created_by": map_obj.created_by,
            "created_at": map_obj.created_at,
            "updated_at": map_obj.updated_at,
            "location_count": count or 0
        }
        maps_with_count.append(MapResponse(**map_dict))
    
    return maps_with_count


@router.post("", response_model=MapResponse, status_code=status.HTTP_201_CREATED)
async def create_map(
    map_data: MapCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Cria um novo mapa.
    """
    new_map = Map(
        name=map_data.name,
        icon=map_data.icon,
        color=map_data.color,
        is_shared=map_data.is_shared,
        created_by=current_user.id
    )
    db.add(new_map)
    await db.commit()
    await db.refresh(new_map)
    
    return MapResponse(
        id=new_map.id,
        name=new_map.name,
        icon=new_map.icon,
        color=new_map.color,
        is_shared=new_map.is_shared,
        created_by=new_map.created_by,
        created_at=new_map.created_at,
        updated_at=new_map.updated_at,
        location_count=0
    )


@router.get("/{map_id}", response_model=MapResponse)
async def get_map(
    map_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retorna um mapa pelo ID.
    """
    result = await db.execute(select(Map).where(Map.id == map_id))
    map_obj = result.scalar_one_or_none()
    
    if not map_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mapa não encontrado"
        )
    
    # Verificar acesso
    if map_obj.created_by != current_user.id:
        result = await db.execute(
            select(MapMember)
            .where(MapMember.map_id == map_id, MapMember.user_id == current_user.id)
        )
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado"
            )
    
    # Contar lugares
    result = await db.execute(
        select(func.count()).select_from(Place).where(Place.map_id == map_id)
    )
    count = result.scalar()
    
    return MapResponse(
        id=map_obj.id,
        name=map_obj.name,
        icon=map_obj.icon,
        color=map_obj.color,
        is_shared=map_obj.is_shared,
        created_by=map_obj.created_by,
        created_at=map_obj.created_at,
        updated_at=map_obj.updated_at,
        location_count=count or 0
    )


@router.put("/{map_id}", response_model=MapResponse)
async def update_map(
    map_id: str,
    map_data: MapUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Atualiza um mapa.
    """
    result = await db.execute(select(Map).where(Map.id == map_id))
    map_obj = result.scalar_one_or_none()
    
    if not map_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mapa não encontrado"
        )
    
    if map_obj.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas o criador pode editar o mapa"
        )
    
    update_data = map_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(map_obj, field, value)
    
    await db.commit()
    await db.refresh(map_obj)
    
    # Contar lugares
    result = await db.execute(
        select(func.count()).select_from(Place).where(Place.map_id == map_id)
    )
    count = result.scalar()
    
    return MapResponse(
        id=map_obj.id,
        name=map_obj.name,
        icon=map_obj.icon,
        color=map_obj.color,
        is_shared=map_obj.is_shared,
        created_by=map_obj.created_by,
        created_at=map_obj.created_at,
        updated_at=map_obj.updated_at,
        location_count=count or 0
    )


@router.delete("/{map_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_map(
    map_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Exclui um mapa.
    """
    result = await db.execute(select(Map).where(Map.id == map_id))
    map_obj = result.scalar_one_or_none()
    
    if not map_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mapa não encontrado"
        )
    
    if map_obj.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas o criador pode excluir o mapa"
        )
    
    await db.delete(map_obj)
    await db.commit()
