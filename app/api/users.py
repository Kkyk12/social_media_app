from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
import model
from schema import UserCreate, UserResponse
import util


router = APIRouter(tags=["Users"])


@router.post("/create_user", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # check if email already exists to avoid DB integrity error
    existing_user = db.query(model.user).filter(model.user.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    hashed_password = util.hash_password(user.password[:72])
    user.password = hashed_password
    new_user = model.user(**user.dict())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
