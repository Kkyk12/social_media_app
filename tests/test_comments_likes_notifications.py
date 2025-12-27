from fastapi import status

import model
from util import hash_password


def create_user(db, email: str, password: str):
    existing = db.query(model.user).filter(model.user.email == email).first()
    if existing:
        db.delete(existing)
        db.commit()
    user = model.user(email=email, password=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_token(client, email: str, password: str) -> str:
    resp = client.post(
        "/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == status.HTTP_200_OK
    return resp.json()["access_token"]


def test_comments_likes_and_notifications(client, db_session):
    # owner creates post, other user comments and likes -> owner gets notifications
    owner = create_user(db_session, "owner@example.com", "owner-pass")
    actor = create_user(db_session, "actor@example.com", "actor-pass")

    owner_token = get_token(client, owner.email, "owner-pass")
    actor_token = get_token(client, actor.email, "actor-pass")

    # owner creates a post
    create_post_resp = client.post(
        "/posts/",
        json={"content": "post for notifications"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert create_post_resp.status_code == status.HTTP_201_CREATED
    post = create_post_resp.json()

    # actor comments
    comment_resp = client.post(
        f"/posts/{post['id']}/comments",
        json={"content": "nice post"},
        headers={"Authorization": f"Bearer {actor_token}"},
    )
    assert comment_resp.status_code == status.HTTP_201_CREATED

    # actor likes
    like_resp = client.post(
        f"/posts/{post['id']}/like",
        headers={"Authorization": f"Bearer {actor_token}"},
    )
    assert like_resp.status_code == status.HTTP_200_OK

    # owner should see notifications for comment and like
    notif_resp = client.get(
        "/notifications/",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert notif_resp.status_code == status.HTTP_200_OK
    notifications = notif_resp.json()
    types = {n["type"] for n in notifications}
    assert "comment" in types
    assert "like" in types
