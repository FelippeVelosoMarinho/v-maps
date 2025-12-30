from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.user import User
from app.models.map import Map
from app.models.place import Place
from app.models.map_member import MapMember
from app.models.group import Group, GroupMember, GroupMap
from app.schemas.map import MapCreate, MapUpdate, MapResponse, MapGroupInfo
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/maps", tags=["Maps"])


async def get_map_group_info(map_id: str, db: AsyncSession) -> list[MapGroupInfo]:
    """Get groups a map is shared with."""
    result = await db.execute(
        select(GroupMap, Group)
        .join(Group, Group.id == GroupMap.group_id)
        .where(GroupMap.map_id == map_id)
    )
    rows = result.all()
    return [
        MapGroupInfo(
            group_id=group.id,
            group_name=group.name,
            group_icon=group.icon
        )
        for _, group in rows
    ]


@router.get("", response_model=list[MapResponse])
async def get_maps(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retorna todos os mapas do usuário (próprios + compartilhados + de grupos).
    """
    # Mapas próprios
    result = await db.execute(
        select(Map).where(Map.created_by == current_user.id)
        .order_by(Map.created_at.desc())
    )
    own_maps = result.scalars().all()
    own_map_ids = {m.id for m in own_maps}
    
    # Mapas onde é membro direto
    result = await db.execute(
        select(Map)
        .join(MapMember, MapMember.map_id == Map.id)
        .where(MapMember.user_id == current_user.id)
    )
    shared_maps = result.scalars().all()
    
    # Mapas compartilhados com grupos onde o usuário é membro
    result = await db.execute(
        select(Map)
        .join(GroupMap, GroupMap.map_id == Map.id)
        .join(GroupMember, GroupMember.group_id == GroupMap.group_id)
        .where(GroupMember.user_id == current_user.id)
    )
    group_maps = result.scalars().all()
    
    # Combinar todos os mapas (sem duplicatas)
    all_map_ids = set()
    all_maps = []
    for m in own_maps:
        if m.id not in all_map_ids:
            all_map_ids.add(m.id)
            all_maps.append(m)
    for m in shared_maps:
        if m.id not in all_map_ids:
            all_map_ids.add(m.id)
            all_maps.append(m)
    for m in group_maps:
        if m.id not in all_map_ids:
            all_map_ids.add(m.id)
            all_maps.append(m)
    
    # Construir resposta com contagem de lugares e info de grupos
    maps_with_count = []
    for map_obj in all_maps:
        result = await db.execute(
            select(func.count()).select_from(Place).where(Place.map_id == map_obj.id)
        )
        count = result.scalar()
        
        # Obter grupos com os quais o mapa é compartilhado
        group_info = await get_map_group_info(map_obj.id, db)
        
        map_dict = {
            "id": map_obj.id,
            "name": map_obj.name,
            "icon": map_obj.icon,
            "color": map_obj.color,
            "is_shared": map_obj.is_shared,
            "is_public": map_obj.is_public,
            "created_by": map_obj.created_by,
            "created_at": map_obj.created_at,
            "updated_at": map_obj.updated_at,
            "location_count": count or 0,
            "shared_with_groups": group_info
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
    Cria um novo mapa. Se group_id for fornecido, compartilha automaticamente com o grupo.
    """
    # If group_id provided, verify user is a member
    if map_data.group_id:
        member_result = await db.execute(
            select(GroupMember)
            .where(GroupMember.group_id == map_data.group_id)
            .where(GroupMember.user_id == current_user.id)
        )
        if not member_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você não é membro deste grupo"
            )
    
    new_map = Map(
        name=map_data.name,
        icon=map_data.icon,
        color=map_data.color,
        is_shared=map_data.is_shared or bool(map_data.group_id),
        created_by=current_user.id
    )
    db.add(new_map)
    await db.flush()
    
    # If group_id provided, share with group
    if map_data.group_id:
        group_map = GroupMap(
            group_id=map_data.group_id,
            map_id=new_map.id,
            shared_by=current_user.id
        )
        db.add(group_map)
    
    await db.commit()
    await db.refresh(new_map)
    
    # Get group info if shared with a group
    group_info = await get_map_group_info(new_map.id, db) if map_data.group_id else []
    
    return MapResponse(
        id=new_map.id,
        name=new_map.name,
        icon=new_map.icon,
        color=new_map.color,
        is_shared=new_map.is_shared,
        is_public=new_map.is_public,
        created_by=new_map.created_by,
        created_at=new_map.created_at,
        updated_at=new_map.updated_at,
        location_count=0,
        shared_with_groups=group_info
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
    
    # Get group info
    group_info = await get_map_group_info(map_obj.id, db)
    
    return MapResponse(
        id=map_obj.id,
        name=map_obj.name,
        icon=map_obj.icon,
        color=map_obj.color,
        is_shared=map_obj.is_shared,
        is_public=map_obj.is_public,
        created_by=map_obj.created_by,
        created_at=map_obj.created_at,
        updated_at=map_obj.updated_at,
        location_count=count or 0,
        shared_with_groups=group_info
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
    
    # Get group info
    group_info = await get_map_group_info(map_obj.id, db)
    
    return MapResponse(
        id=map_obj.id,
        name=map_obj.name,
        icon=map_obj.icon,
        color=map_obj.color,
        is_shared=map_obj.is_shared,
        is_public=map_obj.is_public,
        created_by=map_obj.created_by,
        created_at=map_obj.created_at,
        updated_at=map_obj.updated_at,
        location_count=count or 0,
        shared_with_groups=group_info
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


# ============ Share with Friends ============

@router.post("/{map_id}/share/{user_id}", status_code=status.HTTP_201_CREATED)
async def share_map_with_user(
    map_id: str,
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Compartilha um mapa com um amigo.
    """
    # Check map exists and user owns it
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
            detail="Apenas o criador pode compartilhar o mapa"
        )
    
    # Check if user exists
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    # Check if already shared
    existing = await db.execute(
        select(MapMember)
        .where(MapMember.map_id == map_id)
        .where(MapMember.user_id == user_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mapa já compartilhado com este usuário"
        )
    
    # Create member entry
    member = MapMember(
        map_id=map_id,
        user_id=user_id,
        role="member"
    )
    db.add(member)
    
    # Mark map as shared
    map_obj.is_shared = True
    
    await db.commit()
    
    return {"message": "Mapa compartilhado com sucesso"}


@router.delete("/{map_id}/share/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unshare_map_with_user(
    map_id: str,
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Remove compartilhamento de mapa com um usuário.
    """
    # Check map exists and user owns it
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
            detail="Apenas o criador pode remover compartilhamento"
        )
    
    # Find and remove member
    member_result = await db.execute(
        select(MapMember)
        .where(MapMember.map_id == map_id)
        .where(MapMember.user_id == user_id)
    )
    member = member_result.scalar_one_or_none()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não tem acesso a este mapa"
        )
    
    await db.delete(member)
    
    # Check if map still has members
    members_result = await db.execute(
        select(func.count(MapMember.id)).where(MapMember.map_id == map_id)
    )
    if members_result.scalar() == 0:
        map_obj.is_shared = False
    
    await db.commit()
