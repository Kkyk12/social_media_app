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


def test_messaging_and_notifications(client, db_session):
    # two users mutually follow, start conversation, send message, recipient gets notification
    u1 = create_user(db_session, "msg_user1@example.com", "pass1")
    u2 = create_user(db_session, "msg_user2@example.com", "pass2")

    token1 = get_token(client, u1.email, "pass1")
    token2 = get_token(client, u2.email, "pass2")

    # mutual follow via API
    resp = client.post(
        f"/follow/{u2.id}",
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert resp.status_code == status.HTTP_200_OK

    resp = client.post(
        f"/follow/{u1.id}",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert resp.status_code == status.HTTP_200_OK

    # user1 opens/creates conversation with user2
    conv_resp = client.post(
        f"/conversations/{u2.id}",
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert conv_resp.status_code == status.HTTP_200_OK
    conv = conv_resp.json()
    conv_id = conv["id"]

    # user1 sends a message
    msg_resp = client.post(
        f"/conversations/{conv_id}/messages",
        json={"content": "hello there"},
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert msg_resp.status_code == status.HTTP_201_CREATED
    msg_body = msg_resp.json()
    assert msg_body["content"] == "hello there"

    # user2 lists messages and should see decrypted content
    list_resp = client.get(
        f"/conversations/{conv_id}/messages",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert list_resp.status_code == status.HTTP_200_OK
    msgs = list_resp.json()
    assert any(m["content"] == "hello there" for m in msgs)

    # user2 should have a message notification
    notif_resp = client.get(
        "/notifications/",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert notif_resp.status_code == status.HTTP_200_OK
    notifications = notif_resp.json()
    types = {n["type"] for n in notifications}
    assert "message" in types
