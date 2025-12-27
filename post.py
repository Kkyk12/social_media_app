from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core import security
import model
from schema import (
    PostCreate,
    PostResponse,
    PostWithStats,
    CommentCreate,
    CommentResponse,
    LikeResponse,
)


router = APIRouter(
    prefix="/posts",
    tags=["Posts"],
)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=PostResponse)
def create_post(
    post: PostCreate,
    db: Session = Depends(get_db),
    current_user=Depends(security.get_current_user),
):
    user_id = int(current_user.id)
    from app.core.rate_limiter import rate_limiter

    rate_limiter.check_rate_limit(
        identifier=str(user_id),
        endpoint="create_post",
        limit=30,
        window_seconds=60,
    )

    new_post = model.Post(content=post.content, owner_id=user_id)
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post


@router.get("/", response_model=List[PostWithStats])
def get_posts(
    db: Session = Depends(get_db),
    limit: int = 20,
    offset: int = 0,
):
    posts = (
        db.query(model.Post)
        .order_by(model.Post.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )
    result = []
    for post in posts:
        likes_count = len(post.likes) if post.likes is not None else 0
        comments_count = len(post.comments) if post.comments is not None else 0
        comments_data = [
            {
                "id": c.id,
                "content": c.content,
                "post_id": c.post_id,
                "owner_id": c.owner_id,
                "created_at": c.created_at,
            }
            for c in (post.comments or [])
        ]
        result.append(
            {
                "id": post.id,
                "content": post.content,
                "owner_id": post.owner_id,
                "owner_email": post.owner.email if post.owner is not None else None,
                "created_at": post.created_at,
                "likes_count": likes_count,
                "comments_count": comments_count,
                "comments": comments_data,
            }
        )
    return result


@router.get("/feed", response_model=List[PostWithStats])
def get_feed(
    db: Session = Depends(get_db),
    current_user=Depends(security.get_current_user),
    limit: int = 20,
    offset: int = 0,
):
    current_user_id = int(current_user.id)

    # find users current_user follows
    follow_rows = (
        db.query(model.Follow)
        .filter(model.Follow.follower_id == current_user_id)
        .all()
    )
    followed_ids = [f.following_id for f in follow_rows]

    if not followed_ids:
        return []

    posts = (
        db.query(model.Post)
        .filter(model.Post.owner_id.in_(followed_ids))
        .order_by(model.Post.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )

    result = []
    for post in posts:
        likes_count = len(post.likes) if post.likes is not None else 0
        comments_count = len(post.comments) if post.comments is not None else 0
        comments_data = [
            {
                "id": c.id,
                "content": c.content,
                "post_id": c.post_id,
                "owner_id": c.owner_id,
                "created_at": c.created_at,
            }
            for c in (post.comments or [])
        ]

        result.append(
            {
                "id": post.id,
                "content": post.content,
                "owner_id": post.owner_id,
                "owner_email": post.owner.email if post.owner is not None else None,
                "created_at": post.created_at,
                "likes_count": likes_count,
                "comments_count": comments_count,
                "comments": comments_data,
            }
        )

    return result


@router.get("/me", response_model=List[PostWithStats])
def get_my_posts(
    db: Session = Depends(get_db),
    current_user=Depends(security.get_current_user),
    limit: int = 20,
    offset: int = 0,
):
    posts = (
        db.query(model.Post)
        .filter(model.Post.owner_id == int(current_user.id))
        .order_by(model.Post.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )

    result = []
    for post in posts:
        likes_count = len(post.likes) if post.likes is not None else 0
        comments_count = len(post.comments) if post.comments is not None else 0
        comments_data = [
            {
                "id": c.id,
                "content": c.content,
                "post_id": c.post_id,
                "owner_id": c.owner_id,
                "created_at": c.created_at,
            }
            for c in (post.comments or [])
        ]

        result.append(
            {
                "id": post.id,
                "content": post.content,
                "owner_id": post.owner_id,
                "owner_email": post.owner.email if post.owner is not None else None,
                "created_at": post.created_at,
                "likes_count": likes_count,
                "comments_count": comments_count,
                "comments": comments_data,
            }
        )

    return result


@router.get("/user/{user_id}", response_model=List[PostWithStats])
def get_user_posts(
    user_id: int,
    db: Session = Depends(get_db),
    limit: int = 20,
    offset: int = 0,
):
    posts = (
        db.query(model.Post)
        .filter(model.Post.owner_id == user_id)
        .order_by(model.Post.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )

    result = []
    for post in posts:
        likes_count = len(post.likes) if post.likes is not None else 0
        comments_count = len(post.comments) if post.comments is not None else 0
        comments_data = [
            {
                "id": c.id,
                "content": c.content,
                "post_id": c.post_id,
                "owner_id": c.owner_id,
                "created_at": c.created_at,
            }
            for c in (post.comments or [])
        ]

        result.append(
            {
                "id": post.id,
                "content": post.content,
                "owner_id": post.owner_id,
                "owner_email": post.owner.email if post.owner is not None else None,
                "created_at": post.created_at,
                "likes_count": likes_count,
                "comments_count": comments_count,
                "comments": comments_data,
            }
        )

    return result


@router.get("/{id}", response_model=PostWithStats)
def get_post(id: int, db: Session = Depends(get_db)):
    post = db.query(model.Post).filter(model.Post.id == id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )

    likes_count = len(post.likes) if post.likes is not None else 0
    comments_count = len(post.comments) if post.comments is not None else 0
    comments_data = [
        {
            "id": c.id,
            "content": c.content,
            "post_id": c.post_id,
            "owner_id": c.owner_id,
            "created_at": c.created_at,
        }
        for c in (post.comments or [])
    ]

    return {
        "id": post.id,
        "content": post.content,
        "owner_id": post.owner_id,
        "owner_email": post.owner.email if post.owner is not None else None,
        "created_at": post.created_at,
        "likes_count": likes_count,
        "comments_count": comments_count,
        "comments": comments_data,
    }


@router.put("/{id}", response_model=PostResponse)
def update_post(
    id: int,
    updated_post: PostCreate,
    db: Session = Depends(get_db),
    current_user=Depends(security.get_current_user),
):
    post_query = db.query(model.Post).filter(model.Post.id == id)
    post = post_query.first()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )

    if post.owner_id != int(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this post",
        )

    post_query.update({"content": updated_post.content}, synchronize_session=False)
    db.commit()
    db.refresh(post)
    return post


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
    id: int,
    db: Session = Depends(get_db),
    current_user=Depends(security.get_current_user),
):
    post_query = db.query(model.Post).filter(model.Post.id == id)
    post = post_query.first()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )

    if post.owner_id != int(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this post",
        )

    post_query.delete(synchronize_session=False)
    db.commit()
    return None


@router.post(
    "/{post_id}/comments",
    status_code=status.HTTP_201_CREATED,
    response_model=CommentResponse,
)
def create_comment(
    post_id: int,
    comment: CommentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(security.get_current_user),
):
    user_id = int(current_user.id)
    from app.core.rate_limiter import rate_limiter

    rate_limiter.check_rate_limit(
        identifier=str(user_id),
        endpoint="create_comment",
        limit=60,
        window_seconds=60,
    )

    post = db.query(model.Post).filter(model.Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )

    new_comment = model.Comment(
        content=comment.content,
        post_id=post_id,
        owner_id=int(current_user.id),
    )
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    # notify post owner if different from commenter
    if post.owner_id != int(current_user.id):
        notif = model.Notification(
            user_id=post.owner_id,
            type="comment",
            message=f"New comment on your post (id={post.id})",
        )
        db.add(notif)
        db.commit()
    return new_comment


@router.get("/{post_id}/comments", response_model=List[CommentResponse])
def get_comments_for_post(
    post_id: int,
    db: Session = Depends(get_db),
    limit: int = 20,
    offset: int = 0,
):
    comments = (
        db.query(model.Comment)
        .filter(model.Comment.post_id == post_id)
        .order_by(model.Comment.created_at.asc())
        .limit(limit)
        .offset(offset)
        .all()
    )
    return comments


@router.post(
    "/{post_id}/like",
    status_code=status.HTTP_200_OK,
)
def toggle_like(
    post_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(security.get_current_user),
):
    post = db.query(model.Post).filter(model.Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )

    like_query = db.query(model.Like).filter(
        model.Like.post_id == post_id,
        model.Like.user_id == int(current_user.id),
    )
    existing_like = like_query.first()

    if existing_like:
        # user already liked -> unlike (dislike)
        like_query.delete(synchronize_session=False)
        db.commit()
        return {"status": "unliked"}

    # not liked yet -> like
    new_like = model.Like(post_id=post_id, user_id=int(current_user.id))
    db.add(new_like)
    db.commit()
    # notify post owner if different from liker
    if post.owner_id != int(current_user.id):
        notif = model.Notification(
            user_id=post.owner_id,
            type="like",
            message=f"Your post (id={post.id}) got a new like",
        )
        db.add(notif)
        db.commit()
    return {"status": "liked"}
