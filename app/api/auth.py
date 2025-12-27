from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..core.db import get_db
from ..core import security
from .. import models as model
from ..core.rate_limiter import rate_limiter


router = APIRouter(tags=["Authentication"])


@router.post("/login")
def login(
    user_credentials: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    # rate limit login attempts per username to reduce brute-force attacks
    rate_limiter.check_rate_limit(
        identifier=user_credentials.username,
        endpoint="login",
        limit=5,
        window_seconds=60,
    )

    user = (
        db.query(model.user)
        .filter(model.user.email == user_credentials.username)
        .first()
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid Credentials",
        )
    if not security.verify_password(user_credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid Credentials",
        )

    access_token = security.create_access_token(data={"user_id": user.id})

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout():
    # With stateless JWTs, logout is handled on the client by discarding the token.
    # This endpoint exists mainly so the frontend has an API to call for "logging out".
    return {"detail": "Logged out. Please discard the token on the client."}


__all__ = ["router"]
