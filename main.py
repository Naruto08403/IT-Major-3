from fastapi import FastAPI, Depends, HTTPException
from starlette.responses import RedirectResponse,FileResponse
from sqlalchemy.orm import Session
from typing import List
from fastapi.middleware.cors import CORSMiddleware
from db import database, models, schemas
import os
from routes import bookRoute,categoryRoute
app = FastAPI()

allow_origins = ['http://localhost:8081',
                 'http://192.168.160.77:8081',
                 'http://192.168.254.184:8081']

app.add_middleware(
    CORSMiddleware,
    allow_origins = allow_origins,
    allow_credentials=True,
    allow_methods=["GET","POST","PUT","DELETE","PATCH"],
    allow_headers=["X-Requested-With","Content-Type"]
)


# Dependency to get the database session
def get_db(): 
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

database.init_db()




# @app.post("/downloads/", response_model=schemas.DownloadRecord)
# def create_download_record(download_record: schemas.DownloadRecordCreate, db: Session = Depends(get_db)):
#     db_download_record = models.DownloadRecord(
#         user_id=download_record.user_id,
#         book_id=download_record.book_id
#     )
#     db.add(db_download_record)
#     db.commit()
#     db.refresh(db_download_record)
#     return db_download_record

# @app.get("/downloads/", response_model=List[schemas.DownloadRecord])
# def read_download_records(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
#     download_records = db.query(models.DownloadRecord).offset(skip).limit(limit).all()
#     return download_records


@app.get("/")
async def main():
    return RedirectResponse(url="/docs/")

app.include_router(bookRoute)
app.include_router(categoryRoute)
# app.include_router(userRoute)