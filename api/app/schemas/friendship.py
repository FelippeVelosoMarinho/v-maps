from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from enum import Enum


class FriendshipStatusEnum(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class FriendshipCreate(BaseModel):
    addressee_id: str


class FriendshipUpdate(BaseModel):
    status: FriendshipStatusEnum


class FriendProfile(BaseModel):
    id: str
    username: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None


class FriendUser(BaseModel):
    id: str
    email: str
    profile: Optional[FriendProfile] = None


class FriendshipResponse(BaseModel):
    id: str
    requester_id: str
    addressee_id: str
    status: FriendshipStatusEnum
    created_at: datetime
    updated_at: datetime
    friend: Optional[FriendUser] = None

    class Config:
        from_attributes = True


class FriendResponse(BaseModel):
    """Simplified friend response for listing friends"""
    id: str
    email: str
    username: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    friendship_id: str
    is_online: bool = False

    class Config:
        from_attributes = True


class UserSearchResult(BaseModel):
    id: str
    email: str
    username: Optional[str] = None
    avatar_url: Optional[str] = None
    is_friend: bool = False
    friendship_status: Optional[FriendshipStatusEnum] = None
    friendship_id: Optional[str] = None

    class Config:
        from_attributes = True
