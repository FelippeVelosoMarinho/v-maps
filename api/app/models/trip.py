import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Boolean, Float, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Trip(Base):
    __tablename__ = "trips"
    
    id: Mapped[str] = mapped_column(
        String(36), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    map_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("maps.id", ondelete="CASCADE"),
        nullable=False
    )
    created_by: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    ended_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    # Report fields (Book of Memories)
    rating: Mapped[int] = mapped_column(nullable=True)
    favorite_photos: Mapped[list[str]] = mapped_column(
        String(2000), # Simple JSON string storage or multiple URLs
        nullable=True,
        default="[]"
    )
    useful_links: Mapped[list[str]] = mapped_column(
        String(2000), # Simple JSON string storage or multiple links
        nullable=True,
        default="[]"
    )
    shared_to_feed: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Relationships
    map: Mapped["Map"] = relationship("Map", back_populates="trips")
    creator: Mapped["User"] = relationship("User", back_populates="trips")
    participants: Mapped[list["TripParticipant"]] = relationship(
        "TripParticipant",
        back_populates="trip",
        cascade="all, delete-orphan"
    )
    locations: Mapped[list["TripLocation"]] = relationship(
        "TripLocation",
        back_populates="trip",
        cascade="all, delete-orphan"
    )


class TripParticipant(Base):
    __tablename__ = "trip_participants"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    trip_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("trips.id", ondelete="CASCADE"),
        nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    status: Mapped[str] = mapped_column(String(20), default="invited")  # invited, accepted, declined, left
    
    # Relationships
    trip: Mapped["Trip"] = relationship("Trip", back_populates="participants")
    user: Mapped["User"] = relationship("User", back_populates="trip_participations")


class TripLocation(Base):
    __tablename__ = "trip_locations"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    trip_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("trips.id", ondelete="CASCADE"),
        nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    accuracy: Mapped[float] = mapped_column(Float, default=0.0)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    trip: Mapped["Trip"] = relationship("Trip", back_populates="locations")
    user: Mapped["User"] = relationship("User")
