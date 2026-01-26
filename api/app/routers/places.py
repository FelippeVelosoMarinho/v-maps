from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from app.models.profile import Profile
from math import radians, cos, sin, asin, sqrt
from app.database import get_db
from app.models.user import User
from app.models.map import Map
from app.models.place import Place
from app.models.map_member import MapMember
from app.schemas.place import PlaceCreate, PlaceUpdate, PlaceResponse
from app.utils.dependencies import get_current_user
from app.utils.permissions import check_map_access

router = APIRouter(prefix="/places", tags=["Places"])




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
        if not await check_map_access(db, map_id, current_user.id):
            # Check if map exists for 404
            map_exists = await db.scalar(select(Map.id).where(Map.id == map_id))
            if not map_exists:
                raise HTTPException(status_code=404, detail="Mapa não encontrado")
            raise HTTPException(status_code=403, detail="Acesso negado ao mapa")
            
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
    if not await check_map_access(db, place_data.map_id, current_user.id):
        # Check if map exists for 404
        map_exists = await db.scalar(select(Map.id).where(Map.id == place_data.map_id))
        if not map_exists:
            raise HTTPException(status_code=404, detail="Mapa não encontrado")
        raise HTTPException(status_code=403, detail="Acesso negado ao mapa")
    
    # Buscar a cor do usuário para este mapa
    user_color = "blue"  # Cor padrão
    
    # Se é o dono do mapa
    result = await db.execute(
        select(Map).where(Map.id == place_data.map_id)
    )
    map_obj = result.scalar_one_or_none()
    
    if map_obj and map_obj.created_by == current_user.id:
        user_color = map_obj.color  # Usa a cor do mapa para o dono
    else:
        # Buscar a cor do membro
        result = await db.execute(
            select(MapMember).where(
                and_(
                    MapMember.map_id == place_data.map_id,
                    MapMember.user_id == current_user.id
                )
            )
        )
        member = result.scalar_one_or_none()
        if member:
            user_color = member.color
    
    new_place = Place(
        map_id=place_data.map_id,
        name=place_data.name,
        description=place_data.description,
        lat=place_data.lat,
        lng=place_data.lng,
        address=place_data.address,
        google_place_id=place_data.google_place_id,
        created_by=current_user.id,
        creator_color=user_color
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
    
    if not await check_map_access(db, place.map_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado ao mapa"
        )
    
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


def haversine(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """
    Calcula a distância em km entre dois pontos usando a fórmula de Haversine.
    """
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # Raio da Terra em km
    return c * r


@router.get("/explore/nearby", response_model=list[PlaceResponse])
async def get_nearby_places(
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
    radius_km: float = Query(10.0, description="Raio de busca em km"),
    limit: int = Query(50, le=100, description="Limite de resultados"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retorna lugares públicos próximos à localização informada.
    Busca lugares de mapas compartilhados (públicos).
    """
    # Busca lugares de mapas compartilhados (públicos) ou do próprio usuário
    result = await db.execute(
        select(Place)
        .join(Map, Map.id == Place.map_id)
        .where(
            or_(
                Map.is_shared == True,
                Map.created_by == current_user.id
            )
        )
    )
    all_places = result.scalars().all()
    
    # Filtrar por distância usando Haversine
    nearby_places = []
    for place in all_places:
        distance = haversine(lng, lat, place.lng, place.lat)
        if distance <= radius_km:
            # Add distance as a temporary attribute
            place._distance = distance
            nearby_places.append(place)
    
    # Ordenar por distância e limitar
    nearby_places.sort(key=lambda p: p._distance)
    
    return nearby_places[:limit]
