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


def setup_conversation(client, db_session):
    # helper to create two mutually-following users and a conversation
    u1 = create_user(db_session, "read_unread1@example.com", "pass1")
    u2 = create_user(db_session, "read_unread2@example.com", "pass2")

    token1 = get_token(client, u1.email, "pass1")
    token2 = get_token(client, u2.email, "pass2")

    # mutual follow
    r = client.post(
        f"/follow/{u2.id}",
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert r.status_code == status.HTTP_200_OK

    r = client.post(
        f"/follow/{u1.id}",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert r.status_code == status.HTTP_200_OK

    # create/get conversation
    conv_resp = client.post(
        f"/conversations/{u2.id}",
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert conv_resp.status_code == status.HTTP_200_OK
    conv = conv_resp.json()
    return u1, u2, token1, token2, conv["id"]


def test_unread_count_and_mark_read(client, db_session):
    u1, u2, token1, token2, conv_id = setup_conversation(client, db_session)

    # user1 sends two messages
    for content in ["msg1", "msg2"]:
        resp = client.post(
            f"/conversations/{conv_id}/messages",
            json={"content": content},
            headers={"Authorization": f"Bearer {token1}"},
        )
        assert resp.status_code == status.HTTP_201_CREATED

    # user2 checks unread count
    unread_resp = client.get(
        f"/conversations/{conv_id}/unread_count",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert unread_resp.status_code == status.HTTP_200_OK
    unread = unread_resp.json()["unread_count"]
    assert unread >= 2

    # mark read
    mark_resp = client.post(
        f"/conversations/{conv_id}/mark_read",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert mark_resp.status_code == status.HTTP_200_OK

    # unread count should now be 0
    unread_resp2 = client.get(
        f"/conversations/{conv_id}/unread_count",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert unread_resp2.status_code == status.HTTP_200_OK
    assert unread_resp2.json()["unread_count"] == 0
