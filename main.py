from fastapi import FastAPI, Depends, HTTPException, status
from schema import TextInput, UserCreate, UserResponse
import model
from database import engine, SessionLocal, get_db
from sqlalchemy.orm import Session
import util, auth, oauth2
import post
import follow_profile
import messaging
import notifications


model.Base.metadata.create_all(bind=engine)


app = FastAPI()
app.include_router(auth.router)
app.include_router(post.router)
app.include_router(follow_profile.router)
app.include_router(messaging.router)
app.include_router(notifications.router)


@app.post("/text")
def read_text(data: TextInput):
    return {"received_text": data.text}

@app.get("/sqlalchemy_test")
def sqlalchemy_test(db: Session = Depends(get_db)):
  
    
    return {"message": "SQLAlchemy is working!"}


@app.post("/user_message")
def user_message(data: TextInput, db: Session = Depends(get_db), get_current_user: str = Depends(oauth2.get_current_user)):
    new_text = model.TextData(text=data.text)
    db.add(new_text)
    db.commit()
    db.refresh(new_text)
    return {"id": new_text.id, "text": new_text.text}


@app.post("/create_user", status_code=201, response_model=UserResponse)   
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

