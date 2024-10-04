from pydantic import BaseModel
from typing import List

# Pydantic schema for Category response
class CategoryResponse(BaseModel):
    name: str

    class Config:
        orm_mode = True