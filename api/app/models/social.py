"""
Modelos de interação social: Likes e Comments
"""
import uuid
from datetime import datetime
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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    # Relationships
    check_in: Mapped["CheckIn"] = relationship("CheckIn", back_populates="comments")
    user: Mapped["User"] = relationship("User", back_populates="check_in_comments")
