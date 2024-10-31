from pydantic import BaseModel, conbytes
from typing import List, Optional
from datetime import datetime

class BookBase(BaseModel):
    title: str
    author: str
    description: Optional[str] = None
    published_date: Optional[datetime] = None
    image: conbytes(min_length=1)
    file: conbytes(min_length=1)

class BookResponse(BaseModel):
    id: int  # Changed to int for consistency
    title: str
    author: str
    description: Optional[str] = None
    published_date: Optional[datetime] = None
    image: str
    file: str

    class Config:
        orm_mode = True  # Use orm_mode for Pydantic to work with SQLAlchemy models

class CategoryBase(BaseModel):
    name: str

class CategoryResponse(BaseModel):
    id: int  # Changed to int for consistency
    name: str

    class Config:
        orm_mode = True
