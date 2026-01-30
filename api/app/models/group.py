import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Group(Base):
    """Model for user groups."""
    __tablename__ = "groups"
    
    id: Mapped[str] = mapped_column(
        String(36), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    icon: Mapped[str] = mapped_column(String(50), default="users")
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    owner_id: Mapped[str] = mapped_column(
        String(36), 
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=lambda: datetime.now(timezone.utc), 
        onupdate=lambda: datetime.now(timezone.utc)
    )
    
    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="owned_groups", foreign_keys=[owner_id])
    members: Mapped[list["GroupMember"]] = relationship(
        "GroupMember", 
        back_populates="group",
        cascade="all, delete-orphan"
    )
    shared_maps: Mapped[list["GroupMap"]] = relationship(
        "GroupMap",
        back_populates="group",
        cascade="all, delete-orphan"
    )
    invites: Mapped[list["GroupInvite"]] = relationship(
        "GroupInvite",
        back_populates="group",
        cascade="all, delete-orphan"
    )


class GroupMember(Base):
    """Model for group members."""
    __tablename__ = "group_members"
    
    id: Mapped[str] = mapped_column(
        String(36), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4())
    )
    group_id: Mapped[str] = mapped_column(
        String(36), 
        ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36), 
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    role: Mapped[str] = mapped_column(String(20), default="member")  # owner, admin, member
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    group: Mapped["Group"] = relationship("Group", back_populates="members")
    user: Mapped["User"] = relationship("User", back_populates="group_memberships")


class GroupMap(Base):
    """Model for maps shared with groups."""
    __tablename__ = "group_maps"
    
    id: Mapped[str] = mapped_column(
        String(36), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4())
    )
    group_id: Mapped[str] = mapped_column(
        String(36), 
        ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    map_id: Mapped[str] = mapped_column(
        String(36), 
        ForeignKey("maps.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    shared_by: Mapped[str] = mapped_column(
        String(36), 
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    shared_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    group: Mapped["Group"] = relationship("Group", back_populates="shared_maps")
    map: Mapped["Map"] = relationship("Map", back_populates="group_shares")
    shared_by_user: Mapped["User"] = relationship("User")


class GroupInvite(Base):
    """Model for group invitations."""
    __tablename__ = "group_invites"
    
    id: Mapped[str] = mapped_column(
        String(36), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4())
    )
    group_id: Mapped[str] = mapped_column(
        String(36), 
        ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    invited_user_id: Mapped[str] = mapped_column(
        String(36), 
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    invited_by_id: Mapped[str] = mapped_column(
        String(36), 
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, accepted, rejected
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    responded_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    group: Mapped["Group"] = relationship("Group", back_populates="invites")
    invited_user: Mapped["User"] = relationship("User", foreign_keys=[invited_user_id], back_populates="group_invites_received")
    invited_by: Mapped["User"] = relationship("User", foreign_keys=[invited_by_id])
