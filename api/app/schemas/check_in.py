from pydantic import BaseModel, Field
from datetime import datetime
from app.schemas.profile import ProfileResponse


class CheckInBase(BaseModel):
    comment: str | None = None
    rating: int | None = Field(None, ge=1, le=5, description="Avaliação de 1 a 5 estrelas")


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
    likes_count: int = 0
    comments_count: int = 0
    is_liked: bool = False
