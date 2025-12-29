from pydantic import BaseModel
from datetime import datetime


class MapBase(BaseModel):
    name: str
    icon: str = "mappin"
    color: str = "teal"
    is_shared: bool = False


class MapCreate(MapBase):
    pass


class MapUpdate(BaseModel):
    name: str | None = None
    icon: str | None = None
    color: str | None = None
    is_shared: bool | None = None


class MapResponse(MapBase):
    id: str
    created_by: str
    created_at: datetime
    updated_at: datetime
    location_count: int = 0
    
    class Config:
        from_attributes = True


class MapWithPlaces(MapResponse):
    places: list["PlaceResponse"] = []


from app.schemas.place import PlaceResponse
MapWithPlaces.model_rebuild()
