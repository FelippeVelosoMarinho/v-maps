"""
Schemas para funcionalidades sociais: Likes, Comments, Perfil Público
"""
from pydantic import BaseModel
from datetime import datetime


# =====================
# Check-in Like Schemas
# =====================

class CheckInLikeBase(BaseModel):
    check_in_id: str


class CheckInLikeCreate(CheckInLikeBase):
    pass


class CheckInLikeResponse(CheckInLikeBase):
    id: str
    user_id: str
    username: str | None = None
    avatar_url: str | None = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# =====================
# Check-in Comment Schemas
# =====================

class CheckInCommentBase(BaseModel):
    content: str


class CheckInCommentCreate(CheckInCommentBase):
    check_in_id: str


class CheckInCommentUpdate(BaseModel):
    content: str


class CheckInCommentResponse(BaseModel):
    id: str
    check_in_id: str
    user_id: str
    username: str | None = None
    avatar_url: str | None = None
    content: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# =====================
# Public Profile Schemas
# =====================

class PublicMapResponse(BaseModel):
    """Mapa público visível no perfil"""
    id: str
    name: str
    icon: str
    color: str
    location_count: int
    created_at: datetime
    likes_count: int = 0
    comments_count: int = 0
    is_liked: bool = False
    shared_to_feed: bool = False
    
    class Config:
        from_attributes = True


class PublicCheckInResponse(BaseModel):
    """Check-in público visível no perfil"""
    id: str
    place_name: str
    comment: str | None
    rating: int | None
    photo_url: str | None
    visited_at: datetime
    like_count: int = 0
    comment_count: int = 0
    
    class Config:
        from_attributes = True


class PublicProfileResponse(BaseModel):
    """Perfil público de um usuário"""
    id: str
    user_id: str
    username: str | None
    avatar_url: str | None
    bio: str | None
    created_at: datetime
    
    # Estatísticas
    map_count: int = 0
    check_in_count: int = 0
    friend_count: int = 0
    favorite_count: int = 0
    wish_list_count: int = 0
    
    # Mapas públicos (somente se amigo ou público)
    public_maps: list[PublicMapResponse] = []
    
    # Check-ins recentes
    recent_check_ins: list[PublicCheckInResponse] = []
    
    # Relacionamento com o visualizador
    is_friend: bool = False
    friendship_status: str | None = None  # pending, accepted, rejected
    
    class Config:
        from_attributes = True


# =====================
# Favorite and Wishlist Schemas
# =====================

class UserPlaceInteractionCreate(BaseModel):
    place_id: str


class UserPlaceInteractionResponse(BaseModel):
    id: str
    user_id: str
    place_id: str
    created_at: datetime

    class Config:
        from_attributes = True


# =====================
# Map Member with Color
# =====================

class MapMemberWithColor(BaseModel):
    """Membro do mapa com cor para marcadores"""
    id: str
    user_id: str
    username: str | None = None
    avatar_url: str | None = None
    role: str
    color: str
    joined_at: datetime
    
    class Config:
        from_attributes = True


# =====================
# Place with Creator Info
# =====================

class PlaceWithCreator(BaseModel):
    """Place com informações do criador"""
    id: str
    map_id: str
    name: str
    description: str | None
    lat: float
    lng: float
    address: str | None
    google_place_id: str | None
    created_by: str
    creator_color: str
    creator_username: str | None = None
    creator_avatar_url: str | None = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# =====================
# Trip Book Schemas (Feed)
# =====================

class TripBookResponse(BaseModel):
    """Resumo de uma viagem finalizada para o feed"""
    id: str
    name: str
    description: str | None
    map_id: str
    created_by: str
    started_at: datetime
    ended_at: datetime | None = None
    participants_count: int
    locations: list[dict] # Coordenadas para o traçado
    rating: int | None
    favorite_photos: list[str] = []
    
    # Info do criador
    creator_username: str | None = None
    creator_avatar_url: str | None = None
    shared_to_feed: bool = False
    likes_count: int = 0
    comments_count: int = 0
    is_liked: bool = False
    
    class Config:
        from_attributes = True


# =====================
# Combined Feed Schema
# =====================

from app.schemas.check_in import CheckInWithDetails
from typing import Union

class SocialFeedResponse(BaseModel):
    items: list[Union[CheckInWithDetails, TripBookResponse, PlaceWithCreator, PublicMapResponse]]
