import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Avatar(Base):
    __tablename__ = "avatars"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True  # Um usuário tem apenas um avatar
    )
    
    # Cabelo
    hair_style: Mapped[str] = mapped_column(String(50), default="waves")  # afro, locks, braids, moicano, waves, careca, curly_long
    hair_color: Mapped[str] = mapped_column(String(7), default="#2C1810")  # Hex color
    
    # Físico
    body_type: Mapped[str] = mapped_column(String(50), default="normal")  # gordinho, magro, forte, normal
    
    # Rosto
    face_shape: Mapped[str] = mapped_column(String(50), default="oval")  # quadrado, retangular, redondo, oval
    
    # Olhos
    eye_type: Mapped[str] = mapped_column(String(50), default="normal")  # asiatico, fechado, piscando, normal, arregalado
    eye_color: Mapped[str] = mapped_column(String(7), default="#4A3C31")  # Hex color
    
    # Pele
    skin_tone: Mapped[str] = mapped_column(String(7), default="#F5D5B8")  # Hex color
    
    # Roupa
    clothing_style: Mapped[str] = mapped_column(String(50), default="casual")  # casual, formal, esportivo, estampado
    clothing_color: Mapped[str] = mapped_column(String(7), default="#3B82F6")  # Hex color
    
    # Acessórios opcionais
    has_glasses: Mapped[bool] = mapped_column(default=False)
    has_beard: Mapped[bool] = mapped_column(default=False)
    beard_color: Mapped[str] = mapped_column(String(7), default="#2C1810")  # Hex color
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="avatar")
