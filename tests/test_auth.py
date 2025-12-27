from fastapi import status

import model
from util import hash_password


TEST_USER_EMAIL = "testuser@example.com"
TEST_USER_PASSWORD = "testpassword123"


def create_user(db):
    # clean up any existing user with same email
    existing = db.query(model.user).filter(model.user.email == TEST_USER_EMAIL).first()
    if existing:
        db.delete(existing)
        db.commit()
    user = model.user(email=TEST_USER_EMAIL, password=hash_password(TEST_USER_PASSWORD))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_login_success(client, db_session):
    create_user(db_session)

    response = client.post(
        "/login",
        data={"username": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_login_invalid_credentials(client, db_session):
    create_user(db_session)

    response = client.post(
        "/login",
        data={"username": TEST_USER_EMAIL, "password": "wrong-password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
