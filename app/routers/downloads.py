from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.models import Download
from app.schemas.download import Download, DownloadCreate
from app.database import get_db

router = APIRouter(
    prefix="/downloads",
    tags=["downloads"]
)

@router.get("/", response_model=List[Download])
def get_downloads(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    downloads = db.query(Download).offset(skip).limit(limit).all()
    return downloads

@router.post("/", response_model=Download)
def create_download(download: DownloadCreate, db: Session = Depends(get_db)):
    db_download = Download(**download.dict())
    db.add(db_download)
    db.commit()
    db.refresh(db_download)
    return db_download

@router.get("/{download_id}", response_model=Download)
def read_download(download_id: int, db: Session = Depends(get_db)):
    download = db.query(Download).filter(Download.id == download_id).first()
    if download is None:
        raise HTTPException(status_code=404, detail="Download not found")
    return download

@router.delete("/{download_id}")
def delete_download(download_id: int, db: Session = Depends(get_db)):
    download = db.query(Download).filter(Download.id == download_id).first()
    if download is None:
        raise HTTPException(status_code=404, detail="Download not found")
    db.delete(download)
    db.commit()
    return {"message": "Download deleted"}
