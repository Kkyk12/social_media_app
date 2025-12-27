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


def test_notifications_mark_read_and_mark_all(client, db_session):
    # follower triggers follow notifications, then we mark them read
    user = create_user(db_session, "notif_target@example.com", "pass1")
    follower = create_user(db_session, "notif_follower@example.com", "pass2")

    token_follower = get_token(client, follower.email, "pass2")
    token_user = get_token(client, user.email, "pass1")

    # follower follows user to create notification
    follow_resp = client.post(
        f"/follow/{user.id}",
        headers={"Authorization": f"Bearer {token_follower}"},
    )
    assert follow_resp.status_code == status.HTTP_200_OK

    # list notifications for user
    notif_resp = client.get(
        "/notifications/",
        headers={"Authorization": f"Bearer {token_user}"},
    )
    assert notif_resp.status_code == status.HTTP_200_OK
    notifications = notif_resp.json()
    assert notifications, "Expected at least one notification"

    first_id = notifications[0]["id"]

    # mark single notification read
    mark_resp = client.post(
        f"/notifications/{first_id}/mark_read",
        headers={"Authorization": f"Bearer {token_user}"},
    )
    assert mark_resp.status_code == status.HTTP_200_OK

    # mark all notifications read
    mark_all_resp = client.post(
        "/notifications/mark_all_read",
        headers={"Authorization": f"Bearer {token_user}"},
    )
    assert mark_all_resp.status_code == status.HTTP_200_OK
