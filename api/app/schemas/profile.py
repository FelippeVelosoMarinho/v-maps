from pydantic import BaseModel
from datetime import datetime


class ProfileBase(BaseModel):
    username: str | None = None
    avatar_url: str | None = None
    bio: str | None = None


class ProfileCreate(ProfileBase):
    pass


class ProfileUpdate(ProfileBase):
    pass


class ProfileResponse(ProfileBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
