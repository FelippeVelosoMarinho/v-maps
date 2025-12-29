from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.models.map import Map
from app.models.place import Place
from app.models.map_member import MapMember
from app.schemas.place import PlaceCreate, PlaceUpdate, PlaceResponse
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/places", tags=["Places"])


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


@router.get("", response_model=list[PlaceResponse])
async def get_places(
    map_id: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retorna lugares. Se map_id for fornecido, filtra por mapa.
    """
    if map_id:
        await check_map_access(map_id, current_user.id, db)
        result = await db.execute(
            select(Place).where(Place.map_id == map_id)
            .order_by(Place.created_at.desc())
        )
    else:
        # Retornar lugares de todos os mapas do usuário
        result = await db.execute(
            select(Place)
            .join(Map, Map.id == Place.map_id)
            .where(Map.created_by == current_user.id)
            .order_by(Place.created_at.desc())
        )
    
    places = result.scalars().all()
    return places


@router.post("", response_model=PlaceResponse, status_code=status.HTTP_201_CREATED)
async def create_place(
    place_data: PlaceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Cria um novo lugar.
    """
    await check_map_access(place_data.map_id, current_user.id, db)
    
    new_place = Place(
        map_id=place_data.map_id,
        name=place_data.name,
        description=place_data.description,
        lat=place_data.lat,
        lng=place_data.lng,
        address=place_data.address,
        google_place_id=place_data.google_place_id,
        created_by=current_user.id
    )
    db.add(new_place)
    await db.commit()
    await db.refresh(new_place)
    
    return new_place


@router.get("/{place_id}", response_model=PlaceResponse)
async def get_place(
    place_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retorna um lugar pelo ID.
    """
    result = await db.execute(select(Place).where(Place.id == place_id))
    place = result.scalar_one_or_none()
    
    if not place:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lugar não encontrado"
        )
    
    await check_map_access(place.map_id, current_user.id, db)
    
    return place


@router.put("/{place_id}", response_model=PlaceResponse)
async def update_place(
    place_id: str,
    place_data: PlaceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Atualiza um lugar.
    """
    result = await db.execute(select(Place).where(Place.id == place_id))
    place = result.scalar_one_or_none()
    
    if not place:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lugar não encontrado"
        )
    
    if place.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas o criador pode editar o lugar"
        )
    
    update_data = place_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(place, field, value)
    
    await db.commit()
    await db.refresh(place)
    
    return place


@router.delete("/{place_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_place(
    place_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Exclui um lugar.
    """
    result = await db.execute(select(Place).where(Place.id == place_id))
    place = result.scalar_one_or_none()
    
    if not place:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lugar não encontrado"
        )
    
    if place.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas o criador pode excluir o lugar"
        )
    
    await db.delete(place)
    await db.commit()
