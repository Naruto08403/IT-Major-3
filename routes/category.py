from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from db import schemas, models
from typing import List
from db import database

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

categoryRoute = APIRouter()

@categoryRoute.post("/categories/", response_model=schemas.CategoryResponse,tags=['Category Routers'])
def create_category(category: schemas.CategoryBase, db: Session = Depends(get_db)):
    db_category = models.Category(name=category.name)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

@categoryRoute.get("/categories/", response_model=List[schemas.CategoryResponse],tags=['Category Routers'])
def read_categories(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    categories = db.query(models.Category).offset(skip).limit(limit).all()
    return categories

@categoryRoute.put("/categories/{id}", response_model=schemas.CategoryResponse,tags=['Category Routers'])
def update_category(category: schemas.CategoryBase, db: Session = Depends(get_db)):
    db_category = db.query(schemas.CategoryBase).where(schemas.CategoryBase.id == category.id).first()
    db_category.name = category.name
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

@categoryRoute.delete("/categories/{id}", response_model=List[schemas.CategoryResponse],tags=['Category Routers'])
def delete_categories(id: int = 10, db: Session = Depends(get_db)):
    db.delete(schemas.CategoryBase).where(schemas.CategoryBase.id == id)
    return "Deleted Sucessfully"


