from pydantic import BaseModel
from datetime import datetime


class PlaceBase(BaseModel):
    name: str
    description: str | None = None
    lat: float
    lng: float
    address: str | None = None
    google_place_id: str | None = None


class PlaceCreate(PlaceBase):
    map_id: str


class PlaceUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    address: str | None = None


class PlaceResponse(PlaceBase):
    id: str
    map_id: str
    created_by: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PlaceWithCheckIns(PlaceResponse):
    check_ins: list["CheckInResponse"] = []


from app.schemas.check_in import CheckInResponse
PlaceWithCheckIns.model_rebuild()
