from pydantic import BaseModel

class DownloadBase(BaseModel):
    user_id: int
    book_id: int

class DownloadCreate(DownloadBase):
    pass

class Download(DownloadBase):
    id: int

    class Config:
        orm_mode = True
