from pydantic import BaseModel
from datetime import datetime
from app.schemas.profile import ProfileResponse


class ChatMessageBase(BaseModel):
    content: str


class ChatMessageCreate(ChatMessageBase):
    map_id: str


class ChatMessageResponse(ChatMessageBase):
    id: str
    map_id: str
    user_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class ChatMessageWithProfile(ChatMessageResponse):
    profile: ProfileResponse | None = None
