from pydantic import BaseModel
from datetime import datetime


class MapBase(BaseModel):
    name: str
    icon: str = "mappin"
    color: str = "teal"
    is_shared: bool = False
    is_public: bool = False  # Visível no perfil público


class MapCreate(MapBase):
    group_id: str | None = None  # Optional: create map directly for a group


class MapUpdate(BaseModel):
    name: str | None = None
    icon: str | None = None
    color: str | None = None
    is_shared: bool | None = None
    is_public: bool | None = None


class MapGroupInfo(BaseModel):
    """Info about a group the map is shared with."""
    group_id: str
    group_name: str
    group_icon: str


class MapResponse(MapBase):
    id: str
    created_by: str
    created_at: datetime
    updated_at: datetime
    location_count: int = 0
    shared_with_groups: list[MapGroupInfo] = []  # Groups this map is shared with
    
    class Config:
        from_attributes = True


class MapWithPlaces(MapResponse):
    places: list["PlaceResponse"] = []


from app.schemas.place import PlaceResponse
MapWithPlaces.model_rebuild()
