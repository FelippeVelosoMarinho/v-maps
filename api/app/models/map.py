import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Map(Base):
    __tablename__ = "maps"
    
    id: Mapped[str] = mapped_column(
        String(36), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    icon: Mapped[str] = mapped_column(String(50), default="mappin")
    color: Mapped[str] = mapped_column(String(50), default="teal")
    is_shared: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[str] = mapped_column(
        String(36), 
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    # Relationships
    creator: Mapped["User"] = relationship("User", back_populates="maps")
    places: Mapped[list["Place"]] = relationship(
        "Place", 
        back_populates="map",
        cascade="all, delete-orphan"
    )
    members: Mapped[list["MapMember"]] = relationship(
        "MapMember", 
        back_populates="map",
        cascade="all, delete-orphan"
    )
    invites: Mapped[list["MapInvite"]] = relationship(
        "MapInvite", 
        back_populates="map",
        cascade="all, delete-orphan"
    )
    chat_messages: Mapped[list["ChatMessage"]] = relationship(
        "ChatMessage", 
        back_populates="map",
        cascade="all, delete-orphan"
    )
