from fastapi import APIRouter,Depends, HTTPException
from sqlalchemy.orm import Session
from db import schemas, models, database
from typing import List

from sqlalchemy.exc import IntegrityError



def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

userRoute = APIRouter()

@userRoute.post("/users/", response_model=schemas.User,tags=['User Router'])
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = models.User(username=user.username, email=user.email, hashed_password=user.password)
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email already registered")
    return db_user

@userRoute.get("/users/", response_model=List[schemas.User],tags=['User Router'])
def read_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    users = db.query(models.User).offset(skip).limit(limit).all()
    return users
