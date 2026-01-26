import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"
    
    id: Mapped[str] = mapped_column(
        String(36), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4())
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    # Relationships
    profile: Mapped["Profile"] = relationship(
        "Profile", 
        back_populates="user", 
        uselist=False,
        cascade="all, delete-orphan"
    )
    maps: Mapped[list["Map"]] = relationship(
        "Map", 
        back_populates="creator",
        cascade="all, delete-orphan"
    )
    places: Mapped[list["Place"]] = relationship(
        "Place", 
        back_populates="creator",
        cascade="all, delete-orphan"
    )
    check_ins: Mapped[list["CheckIn"]] = relationship(
        "CheckIn", 
        back_populates="user",
        cascade="all, delete-orphan"
    )
    chat_messages: Mapped[list["ChatMessage"]] = relationship(
        "ChatMessage", 
        back_populates="user",
        cascade="all, delete-orphan"
    )
    map_memberships: Mapped[list["MapMember"]] = relationship(
        "MapMember", 
        back_populates="user",
        cascade="all, delete-orphan"
    )
    sent_friend_requests: Mapped[list["Friendship"]] = relationship(
        "Friendship",
        foreign_keys="Friendship.requester_id",
        back_populates="requester",
        cascade="all, delete-orphan"
    )
    received_friend_requests: Mapped[list["Friendship"]] = relationship(
        "Friendship",
        foreign_keys="Friendship.addressee_id",
        back_populates="addressee",
        cascade="all, delete-orphan"
    )
    owned_groups: Mapped[list["Group"]] = relationship(
        "Group",
        foreign_keys="Group.owner_id",
        back_populates="owner",
        cascade="all, delete-orphan"
    )
    group_memberships: Mapped[list["GroupMember"]] = relationship(
        "GroupMember",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    group_invites_received: Mapped[list["GroupInvite"]] = relationship(
        "GroupInvite",
        foreign_keys="GroupInvite.invited_user_id",
        back_populates="invited_user",
        cascade="all, delete-orphan"
    )
    # Social interactions
    check_in_likes: Mapped[list["CheckInLike"]] = relationship(
        "CheckInLike",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    check_in_comments: Mapped[list["CheckInComment"]] = relationship(
        "CheckInComment",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    # Trips
    trips: Mapped[list["Trip"]] = relationship(
        "Trip",
        back_populates="creator",
        cascade="all, delete-orphan"
    )
    trip_participations: Mapped[list["TripParticipant"]] = relationship(
        "TripParticipant",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    avatar: Mapped["Avatar"] = relationship(
        "Avatar",
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False  # One-to-one relationship
    )
    # User Social (Favorites and Wishlist)
    favorite_places: Mapped[list["FavoritePlace"]] = relationship(
        "FavoritePlace",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    wish_list_places: Mapped[list["WishListPlace"]] = relationship(
        "WishListPlace",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    notifications: Mapped[list["Notification"]] = relationship(
        "Notification",
        back_populates="user",
        cascade="all, delete-orphan"
    )
