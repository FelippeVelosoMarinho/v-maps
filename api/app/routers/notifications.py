from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List

from app.database import get_db
from app.models import Notification
from app.schemas.notification import NotificationResponse, NotificationUpdate
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=List[NotificationResponse])
async def get_notifications(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Fetch all notifications for the current user"""
    result = await db.execute(
        select(Notification)
        .where(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
    )
    return result.scalars().all()


@router.patch("/{notification_id}", response_model=NotificationResponse)
async def update_notification(
    notification_id: str,
    notification_update: NotificationUpdate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark a notification as read/unread"""
    result = await db.execute(
        select(Notification).where(
            (Notification.id == notification_id) & 
            (Notification.user_id == current_user.id)
        )
    )
    notification = result.scalar_one_or_none()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
        
    notification.is_read = notification_update.is_read
    await db.commit()
    await db.refresh(notification)
    
    return notification


@router.post("/mark-all-read")
async def mark_all_read(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark all notifications for the current user as read"""
    await db.execute(
        update(Notification)
        .where(Notification.user_id == current_user.id)
        .values(is_read=True)
    )
    await db.commit()
    return {"message": "All notifications marked as read"}
