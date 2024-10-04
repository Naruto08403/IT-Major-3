from pydantic import BaseModel
from typing import List
from datetime import datetime


# Pydantic schema for Book response
class BookResponse(BaseModel):
    title: str
    description: str
    created_at: datetime
    image: str = None
    file: str = None
    categories: list[str] = []
    download_count:int

    class Config:
        orm_mode = True