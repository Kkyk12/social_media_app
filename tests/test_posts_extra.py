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


def test_posts_me_user_feed_and_comments_listing(client, db_session):
    # create three users: me, other (followed), third (not followed)
    me = create_user(db_session, "posts_me@example.com", "pass1")
    other = create_user(db_session, "posts_other@example.com", "pass2")
    third = create_user(db_session, "posts_third@example.com", "pass3")

    token_me = get_token(client, me.email, "pass1")
    token_other = get_token(client, other.email, "pass2")

    # me follows other so feed should include other's posts
    follow_resp = client.post(
        f"/follow/{other.id}",
        headers={"Authorization": f"Bearer {token_me}"},
    )
    assert follow_resp.status_code == status.HTTP_200_OK

    # each user creates a post
    me_post_resp = client.post(
        "/posts/",
        json={"content": "my post"},
        headers={"Authorization": f"Bearer {token_me}"},
    )
    assert me_post_resp.status_code == status.HTTP_201_CREATED
    me_post = me_post_resp.json()

    other_post_resp = client.post(
        "/posts/",
        json={"content": "other post"},
        headers={"Authorization": f"Bearer {token_other}"},
    )
    assert other_post_resp.status_code == status.HTTP_201_CREATED
    other_post = other_post_resp.json()

    # /posts/me should include my post
    me_list_resp = client.get(
        "/posts/me",
        headers={"Authorization": f"Bearer {token_me}"},
    )
    assert me_list_resp.status_code == status.HTTP_200_OK
    me_posts = me_list_resp.json()
    assert any(p["id"] == me_post["id"] for p in me_posts)

    # /posts/user/{user_id} for other should include other's post
    other_list_resp = client.get(f"/posts/user/{other.id}")
    assert other_list_resp.status_code == status.HTTP_200_OK
    other_posts = other_list_resp.json()
    assert any(p["id"] == other_post["id"] for p in other_posts)

    # feed for me should include followed user's post
    feed_resp = client.get(
        "/posts/feed",
        headers={"Authorization": f"Bearer {token_me}"},
    )
    assert feed_resp.status_code == status.HTTP_200_OK
    feed_posts = feed_resp.json()
    assert any(p["id"] == other_post["id"] for p in feed_posts)

    # comments listing: add a comment then list it
    comment_resp = client.post(
        f"/posts/{me_post['id']}/comments",
        json={"content": "comment 1"},
        headers={"Authorization": f"Bearer {token_other}"},
    )
    assert comment_resp.status_code == status.HTTP_201_CREATED

    comments_list_resp = client.get(f"/posts/{me_post['id']}/comments")
    assert comments_list_resp.status_code == status.HTTP_200_OK
    comments = comments_list_resp.json()
    assert any(c["content"] == "comment 1" for c in comments)
