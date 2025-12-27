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


def get_token_for_user(client, email: str, password: str) -> str:
    response = client.post(
        "/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == status.HTTP_200_OK
    return response.json()["access_token"]


def test_create_and_list_posts(client, db_session):
    email = "poster@example.com"
    password = "poster-pass"
    create_user(db_session, email, password)
    token = get_token_for_user(client, email, password)

    # create post
    create_resp = client.post(
        "/posts/",
        json={"content": "hello world"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create_resp.status_code == status.HTTP_201_CREATED
    post_body = create_resp.json()
    assert post_body["content"] == "hello world"

    # list posts
    list_resp = client.get("/posts/")
    assert list_resp.status_code == status.HTTP_200_OK
    posts = list_resp.json()
    assert any(p["id"] == post_body["id"] for p in posts)
