import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class CheckIn(Base):
    __tablename__ = "check_ins"
    
    id: Mapped[str] = mapped_column(
        String(36), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4())
    )
    place_id: Mapped[str] = mapped_column(
        String(36), 
        ForeignKey("places.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36), 
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    photo_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1-5 estrelas
    visited_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    place: Mapped["Place"] = relationship("Place", back_populates="check_ins")
    user: Mapped["User"] = relationship("User", back_populates="check_ins")
    likes: Mapped[list["CheckInLike"]] = relationship(
        "CheckInLike",
        back_populates="check_in",
        cascade="all, delete-orphan"
    )
    comments: Mapped[list["CheckInComment"]] = relationship(
        "CheckInComment",
        back_populates="check_in",
        cascade="all, delete-orphan",
        order_by="CheckInComment.created_at"
    )
