from pydantic import BaseModel
from datetime import datetime


# ============ Group Schemas ============

class GroupBase(BaseModel):
    name: str
    icon: str = "users"
    description: str | None = None


class GroupCreate(GroupBase):
    """Schema for creating a group."""
    member_ids: list[str] = []  # Optional list of user IDs to add as members


class GroupUpdate(BaseModel):
    """Schema for updating a group."""
    name: str | None = None
    icon: str | None = None
    description: str | None = None


class GroupMemberInfo(BaseModel):
    """Schema for group member info."""
    id: str
    user_id: str
    role: str
    joined_at: datetime
    username: str | None = None
    avatar_url: str | None = None
    
    class Config:
        from_attributes = True


class GroupResponse(GroupBase):
    """Schema for group response."""
    id: str
    owner_id: str
    created_at: datetime
    updated_at: datetime
    member_count: int = 0
    
    class Config:
        from_attributes = True


class GroupWithMembers(GroupResponse):
    """Schema for group response with members."""
    members: list[GroupMemberInfo] = []


class GroupMapInfo(BaseModel):
    """Schema for map shared with group."""
    id: str
    map_id: str
    map_name: str
    map_icon: str
    shared_by: str
    shared_by_username: str | None = None
    shared_at: datetime
    
    class Config:
        from_attributes = True


class GroupWithMaps(GroupWithMembers):
    """Schema for group response with members and shared maps."""
    shared_maps: list[GroupMapInfo] = []


# ============ Member Schemas ============

class GroupMemberCreate(BaseModel):
    """Schema for adding a member to a group."""
    user_id: str
    role: str = "member"


class GroupMemberUpdate(BaseModel):
    """Schema for updating a member's role."""
    role: str


# ============ Map Sharing Schemas ============

class ShareMapWithGroup(BaseModel):
    """Schema for sharing a map with a group."""
    map_id: str
