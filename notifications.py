from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core import security
import model
from schema import NotificationResponse


router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
)


@router.get("/", response_model=List[NotificationResponse])
def list_notifications(
    db: Session = Depends(get_db),
    current_user=Depends(security.get_current_user),
    limit: int = 20,
    offset: int = 0,
):
    current_user_id = int(current_user.id)

    notifications = (
        db.query(model.Notification)
        .filter(model.Notification.user_id == current_user_id)
        .order_by(model.Notification.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )
    return notifications


@router.post("/{notification_id}/mark_read", status_code=status.HTTP_200_OK)
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(security.get_current_user),
):
    current_user_id = int(current_user.id)

    notif_query = db.query(model.Notification).filter(
        model.Notification.id == notification_id,
        model.Notification.user_id == current_user_id,
    )
    notif = notif_query.first()
    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    notif_query.update({"is_read": True}, synchronize_session=False)
    db.commit()
    return {"detail": "Notification marked as read"}


@router.post("/mark_all_read", status_code=status.HTTP_200_OK)
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user=Depends(security.get_current_user),
):
    current_user_id = int(current_user.id)

    (
        db.query(model.Notification)
        .filter(
            model.Notification.user_id == current_user_id,
            model.Notification.is_read == False,
        )
        .update({"is_read": True}, synchronize_session=False)
    )
    db.commit()
    return {"detail": "All notifications marked as read"}
