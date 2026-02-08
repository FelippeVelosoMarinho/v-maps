"""
Modelos de interação social: Likes e Comments
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class CheckInLike(Base):
    """Curtidas em check-ins"""
    __tablename__ = "check_in_likes"
    
    id: Mapped[str] = mapped_column(
        String(36), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4())
    )
    check_in_id: Mapped[str] = mapped_column(
        String(36), 
        ForeignKey("check_ins.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36), 
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    check_in: Mapped["CheckIn"] = relationship("CheckIn", back_populates="likes")
    user: Mapped["User"] = relationship("User", back_populates="check_in_likes")


class CheckInComment(Base):
    """Comentários em check-ins"""
    __tablename__ = "check_in_comments"
    
    id: Mapped[str] = mapped_column(
        String(36), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4())
    )
    check_in_id: Mapped[str] = mapped_column(
        String(36), 
        ForeignKey("check_ins.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36), 
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=lambda: datetime.now(timezone.utc), 
        onupdate=lambda: datetime.now(timezone.utc)
    )
    
    # Relationships
    check_in: Mapped["CheckIn"] = relationship("CheckIn", back_populates="comments")
    user: Mapped["User"] = relationship("User", back_populates="check_in_comments")


class TripLike(Base):
    """Curtidas em Trips (Viagens acompanhadas)"""
    __tablename__ = "trip_likes"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    trip_id: Mapped[str] = mapped_column(String(36), ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship("User")


class TripComment(Base):
    """Comentários em Trips"""
    __tablename__ = "trip_comments"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    trip_id: Mapped[str] = mapped_column(String(36), ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship("User")


class MapLike(Base):
    """Curtidas em Mapas compartilhados"""
    __tablename__ = "map_likes"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    map_id: Mapped[str] = mapped_column(String(36), ForeignKey("maps.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship("User")


class MapComment(Base):
    """Comentários em Mapas compartilhados"""
    __tablename__ = "map_comments"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    map_id: Mapped[str] = mapped_column(String(36), ForeignKey("maps.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship("User")


class SocialPost(Base):
    """
    Unified Social Post model.
    Wraps content (CheckIn, Trip, Map) or stands alone (text post? for now only wrappers).
    Allows Reposts and unified Feed.
    """
    __tablename__ = "social_posts"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Content Reference
    content_type: Mapped[str] = mapped_column(String(50), nullable=False) # 'check_in', 'trip', 'map'
    content_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    
    # Metadata
    caption: Mapped[str] = mapped_column(Text, nullable=True) # User's caption for the post/repost
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", backref="social_posts")
    
    # Interactions
    likes: Mapped[list["SocialPostLike"]] = relationship("SocialPostLike", back_populates="post", cascade="all, delete-orphan")
    comments: Mapped[list["SocialPostComment"]] = relationship("SocialPostComment", back_populates="post", cascade="all, delete-orphan")


class SocialPostLike(Base):
    __tablename__ = "social_post_likes"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    post_id: Mapped[str] = mapped_column(String(36), ForeignKey("social_posts.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    post: Mapped["SocialPost"] = relationship("SocialPost", back_populates="likes")
    user: Mapped["User"] = relationship("User")


class SocialPostComment(Base):
    __tablename__ = "social_post_comments"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    post_id: Mapped[str] = mapped_column(String(36), ForeignKey("social_posts.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    post: Mapped["SocialPost"] = relationship("SocialPost", back_populates="comments")
    user: Mapped["User"] = relationship("User")
