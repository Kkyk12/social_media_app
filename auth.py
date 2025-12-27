from fastapi import FastAPI, Depends, status, HTTPException, Response, APIRouter
from sqlalchemy.orm import Session
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
import database
import util
import model,oauth2
from schema import UserLogin
import rate_limiter


router = APIRouter(
    tags=["Authentication"]
)

@router.post("/login")
def login(user_credentials :OAuth2PasswordRequestForm= Depends(),db: Session = Depends(database.get_db)):
    # rate limit login attempts per username to reduce brute-force attacks
    rate_limiter.check_rate_limit(
        identifier=user_credentials.username,
        endpoint="login",
        limit=5,
        window_seconds=60,
    )

    user = db.query(model.user).filter(model.user.email == user_credentials.username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials")
    if not util.verify_password(user_credentials.password, user.password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials")
    

    access_token = oauth2.create_access_token(data={"user_id": user.id})


    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout():
    # With stateless JWTs, logout is handled on the client by discarding the token.
    # This endpoint exists mainly so the frontend has an API to call for "logging out".
    return {"detail": "Logged out. Please discard the token on the client."}
