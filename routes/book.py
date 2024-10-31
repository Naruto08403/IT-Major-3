from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from db.models import session, Book, Category
from db.schemas import BookBase, BookResponse, CategoryBase, CategoryResponse
from typing import List
import os
from datetime import datetime

UPLOAD_DIRECTORY = "./uploads"
bookRoute = APIRouter()

def save_file(uploaded_file: UploadFile, directory: str) -> str:
    file_location = os.path.join(directory, uploaded_file.filename)
    with open(file_location, "wb") as f:
        f.write(uploaded_file.file.read())
    return file_location

def add_book(book: BookBase, categories: List[CategoryBase], db: Session):
    # Save the image and file
    image_location = save_file(book.image, UPLOAD_DIRECTORY)
    file_location = save_file(book.file, UPLOAD_DIRECTORY)

    # Create a new book instance
    new_book = Book(
        title=book.title,
        author=book.author,
        description=book.description,
        published_date=book.published_date,
        file=file_location,
        image=image_location,
    )
    
    # Add categories to the new book
    for category in categories:
        cat = db.query(Category).filter(Category.name == category.name).first()
        if not cat:
            cat = Category(name=category.name)  # Create new category if it doesn't exist
        new_book.categories.append(cat)  # Associate category with the book

    db.add(new_book)
    db.commit()
    db.refresh(new_book)  # Refresh to get the updated instance
    return new_book  # Optionally return the created book

def get_books_by_category(category_name: str, db: Session) -> List[BookResponse]:
    category = db.query(Category).filter(Category.name == category_name).first()
    if category:
        return [BookResponse.from_orm(book) for book in category.books]  # Return list of books in that category
    return []  # Return empty list if no category found

def delete_book(book_id: int, db: Session):
    # Find the book by ID
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    db.delete(book)  # Remove the book from the session
    db.commit()  # Commit the changes to the database
    return {"detail": "Book deleted successfully"}

@bookRoute.post("/books", response_model=BookResponse, tags=['Book Routers'])
async def create_book(
    book: BookBase,
    categories: List[CategoryBase],
    image: UploadFile = File(...),  # Accept image file
    file: UploadFile = File(...),    # Accept book file
    
):
     # Save the image and file
    image_location = f"./uploads/{image.filename}"
    file_location = f"./uploads/{file.filename}"
    
    with open(image_location, "wb") as img:
        img.write(await image.read())  # Save image

    with open(file_location, "wb") as f:
        f.write(await file.read())  # Save file

    return add_book(book, categories, session)  # Use the new add_book function

@bookRoute.get("/books/category/{category_name}", response_model=List[BookResponse], tags=['Book Routers'])
def read_books_by_category(category_name: str, db: Session = Depends(lambda: session)):
    return get_books_by_category(category_name, db)  # Use the new get_books_by_category function

@bookRoute.get("/books", response_model=List[BookResponse], tags=['Book Routers'])
def read_books(skip: int = 0, limit: int = 10, db: Session = Depends(lambda: session)):
    books = db.query(Book).offset(skip).limit(limit).all()
    return books

@bookRoute.get("/uploads/{image_name}")
async def get_image(image_name: str):
    image_path = os.path.join(UPLOAD_DIRECTORY, image_name)
    if os.path.exists(image_path):
        return FileResponse(image_path)
    else:
        raise HTTPException(status_code=404, detail="Image not found.")

@bookRoute.get("/books/search/", response_model=List[BookResponse])
def search_books(query: str, db: Session = Depends(lambda: session)):
    books = db.query(Book).filter(
        (Book.title.contains(query)) | (Book.author.contains(query))
    ).all()
    return books

@bookRoute.get("/download/{filename}")
async def download_file(filename: str):
    file_path = os.path.join(UPLOAD_DIRECTORY, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, filename=filename)
    else:
        raise HTTPException(status_code=404, detail="File not found.")
