from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List
import json


class TripLocationResponse(BaseModel):
    id: str
    user_id: str
    latitude: float
    longitude: float
    accuracy: float
    recorded_at: datetime


from app.schemas.user import UserWithProfile

class TripParticipantResponse(BaseModel):
    id: str
    user_id: str
    joined_at: datetime
    status: str
    user: Optional[UserWithProfile] = None


class TripCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    map_id: str
    participant_ids: Optional[list[str]] = []
    invite_all: bool = False


class TripUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class TripResponse(BaseModel):
    id: str
    name: str
    description: str
    map_id: str
    created_by: str
    is_active: bool
    started_at: datetime
    ended_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    participants: list[TripParticipantResponse]
    locations: list[TripLocationResponse]
    
    # Report fields
    rating: Optional[int] = None
    favorite_photos: Optional[List[str]] = []
    useful_links: Optional[List[str]] = []

    from pydantic import model_validator

    @model_validator(mode='before')
    @classmethod
    def validate_to_json(cls, data):
        if hasattr(data, 'favorite_photos') and isinstance(data.favorite_photos, str):
            try:
                data.favorite_photos = json.loads(data.favorite_photos)
            except:
                data.favorite_photos = []
        if hasattr(data, 'useful_links') and isinstance(data.useful_links, str):
            try:
                data.useful_links = json.loads(data.useful_links)
            except:
                data.useful_links = []
        return data
    
    class Config:
        from_attributes = True


class AddParticipantsRequest(BaseModel):
    user_ids: list[str]


class LocationUpdate(BaseModel):
    latitude: float
    longitude: float
    accuracy: float = 0.0


class TripReportSubmit(BaseModel):
    rating: int
    favorite_photos: List[str]
    useful_links: List[str]
