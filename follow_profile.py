from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core import security
import model
from schema import ProfileResponse, UserBasic


router = APIRouter(
    tags=["Profile", "Follow"],
)


@router.post("/follow/{user_id}", status_code=status.HTTP_200_OK)
def toggle_follow(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(security.get_current_user),
):
    current_user_id = int(current_user.id)
    if user_id == current_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot follow yourself",
        )

    target_user = db.query(model.user).filter(model.user.id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    follow_query = db.query(model.Follow).filter(
        model.Follow.follower_id == current_user_id,
        model.Follow.following_id == user_id,
    )
    existing = follow_query.first()

    if existing:
        follow_query.delete(synchronize_session=False)
        db.commit()
        return {"status": "unfollowed"}

    new_follow = model.Follow(follower_id=current_user_id, following_id=user_id)
    db.add(new_follow)
    # create notification for the user being followed
    notif = model.Notification(
        user_id=user_id,
        type="follow",
        message=f"{current_user_id} started following you",
    )
    db.add(notif)
    db.commit()
    return {"status": "followed"}


def _build_profile(user_obj: model.user, db: Session) -> ProfileResponse:
    followers = (
        db.query(model.Follow)
        .filter(model.Follow.following_id == user_obj.id)
        .all()
    )
    following = (
        db.query(model.Follow)
        .filter(model.Follow.follower_id == user_obj.id)
        .all()
    )

    follower_users: List[UserBasic] = [
        UserBasic(id=f.follower.id, email=f.follower.email) for f in followers
    ]
    following_users: List[UserBasic] = [
        UserBasic(id=f.following.id, email=f.following.email) for f in following
    ]

    return ProfileResponse(
        user=UserBasic(id=user_obj.id, email=user_obj.email),
        followers_count=len(follower_users),
        following_count=len(following_users),
        followers=follower_users,
        following=following_users,
    )


@router.get("/profile/me", response_model=ProfileResponse)
def get_my_profile(
    db: Session = Depends(get_db),
    current_user=Depends(security.get_current_user),
):
    user_obj = db.query(model.user).filter(model.user.id == int(current_user.id)).first()
    if not user_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return _build_profile(user_obj, db)


@router.get("/profile/{user_id}", response_model=ProfileResponse)
def get_user_profile(user_id: int, db: Session = Depends(get_db)):
    user_obj = db.query(model.user).filter(model.user.id == user_id).first()
    if not user_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return _build_profile(user_obj, db)
