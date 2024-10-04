from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.models import Category 
from app.schemas.category import CategoryOut, CategoryCreate
from app.database import get_db

router = APIRouter(
    prefix="/categories",
    tags=["categories"]
)
# # Route to get all categories
# @app.get("/categories", response_model=list[CategoryResponse])
# async def get_categories():
#     db = SessionLocal()
#     categories = db.query(Category).all()
#     return categories