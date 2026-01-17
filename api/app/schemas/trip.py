from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class TripLocationResponse(BaseModel):
    id: str
    user_id: str
    latitude: float
    longitude: float
    accuracy: float
    recorded_at: datetime


class TripParticipantResponse(BaseModel):
    id: str
    user_id: str
    joined_at: datetime


class TripCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    map_id: str
    participant_ids: Optional[list[str]] = []


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
    
    class Config:
        from_attributes = True


class AddParticipantsRequest(BaseModel):
    user_ids: list[str]


class LocationUpdate(BaseModel):
    latitude: float
    longitude: float
    accuracy: float = 0.0
