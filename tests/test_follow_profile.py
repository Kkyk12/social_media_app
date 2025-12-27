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


def test_follow_and_profiles(client, db_session):
    # create two users
    u1 = create_user(db_session, "follow_tester1@example.com", "pass1")
    u2 = create_user(db_session, "follow_tester2@example.com", "pass2")

    token1 = get_token(client, u1.email, "pass1")

    # follow u2 from u1
    resp = client.post(
        f"/follow/{u2.id}",
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert resp.status_code == status.HTTP_200_OK
    body = resp.json()
    assert body["status"] in {"followed", "unfollowed"}

    # check profile/me for u1
    me_resp = client.get(
        "/profile/me",
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert me_resp.status_code == status.HTTP_200_OK
    me_data = me_resp.json()
    assert me_data["user"]["id"] == u1.id

    # public profile for u2
    other_resp = client.get(f"/profile/{u2.id}")
    assert other_resp.status_code == status.HTTP_200_OK
    other_data = other_resp.json()
    assert other_data["user"]["id"] == u2.id
