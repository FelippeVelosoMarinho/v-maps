from pydantic import BaseModel
from datetime import datetime
from app.schemas.profile import ProfileResponse


class CheckInBase(BaseModel):
    comment: str | None = None


class CheckInCreate(CheckInBase):
    place_id: str


class CheckInResponse(CheckInBase):
    id: str
    place_id: str
    user_id: str
    photo_url: str | None = None
    visited_at: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


class CheckInWithDetails(CheckInResponse):
    profile: ProfileResponse | None = None
    place_name: str | None = None
    map_id: str | None = None
