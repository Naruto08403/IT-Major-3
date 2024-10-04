from fastapi import APIRouter, Depends, HTTPException,UploadFile,File,Form,status
from fastapi.responses import JSONResponse,FileResponse
from sqlalchemy.orm import Session
from typing import List
from app.models import Book, Category, SessionLocal, Download
from app.schemas.books import BookResponse
import shutil
import os
from sqlalchemy import func
# Upload folder
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = APIRouter(  
    prefix="/books",
    tags=["books"]  
)


# Helper function to save files
def save_file(file: UploadFile, folder: str):
    file_location = os.path.join(folder, file.filename)
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return file_location

# Route to add a book with multiple categories
@app.post("/", response_class=JSONResponse)
async def add_book(
    title: str = Form(...),
    description: str = Form(...),
    categories: str = Form(...),   # Comma-separated category names
    image: UploadFile = File(...),  # Image file is required
    file: UploadFile = File(...),   # PDF file is required
):
    db = SessionLocal()

    # Save the image and the PDF file
    image_path = save_file(image, UPLOAD_FOLDER)
    file_path = save_file(file, UPLOAD_FOLDER)

    # Parse and create categories
    category_names = [cat.strip() for cat in categories.split(',')]
    print(category_names)
    category_objs = []
    for name in category_names:
        category = db.query(Category).filter(Category.name == name).first()
        if not category:
            category = Category(name=name)
            db.add(category)
        category_objs.append(category)

    # Create a new book entry
    new_book = Book(
        title=title,
        description=description,
        image=image_path,
        file=file_path,
        categories=category_objs
    )
    print(new_book.categories)

    db.add(new_book)
    db.commit()
    db.refresh(new_book)

    return {"message": "Book added successfully"}

# Route to get all books
@app.get("/", response_model=list[BookResponse])
async def get_books():
    db = SessionLocal()
    books = db.query(Book).all()
    # Convert categories to list of names
    books_with_category_names = []
    for book in books:
        book_data = {
            'title': book.title,
            'description': book.description,
            'created_at': book.created_at,
            'image': book.image,
            'file': book.file,
            'categories': [category.name for category in book.categories],
            'download_count':book.download_count
        }
        books_with_category_names.append(book_data)
    
    return books_with_category_names


# New Route to get books based on a given category
@app.get("/by-category", response_model=list[BookResponse])
async def get_books_by_category(category_name: str ):
    db = SessionLocal()
    
    # Fetch the category by its name
    search_pattern = f"%{category_name}%"
    category = db.query(Category).filter(Category.name.ilike(search_pattern)).first()

    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Get all books related to the category
    books = category.books
    # Convert categories to list of names
    books_with_category_names = []
    for book in books:
        book_data = {
            'title': book.title,
            'description': book.description,
            'created_at': book.created_at,
            'image': book.image,
            'file': book.file,
            'categories': [category.name for category in book.categories],
            'download_count':book.download_count
        }
        books_with_category_names.append(book_data)
    
    return books_with_category_names

# Delete route for a book by ID
@app.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(book_id: int):
    db = SessionLocal()

    # Find the book by its ID
    book = db.query(Book).filter(Book.id == book_id).first()

    # If book not found, return 404
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # Check if any other books share the same image file path
    if book.image:
        image_usage_count = db.query(func.count(Book.id)).filter(Book.image == book.image).scalar()
        if image_usage_count == 1:  # Only delete if this is the only book using the image
            if os.path.exists(book.image):
                try:
                    os.remove(book.image)
                except Exception as e:
                    raise HTTPException(status_code=500, detail=f"Error deleting image file: {e}")

    # Check if any other books share the same PDF file path
    if book.file:
        file_usage_count = db.query(func.count(Book.id)).filter(Book.file == book.file).scalar()
        if file_usage_count == 1:  # Only delete if this is the only book using the PDF
            if os.path.exists(book.file):
                try:
                    os.remove(book.file)
                except Exception as e:
                    raise HTTPException(status_code=500, detail=f"Error deleting PDF file: {e}")

    # Delete the book from the database
    db.delete(book)
    db.commit()

    # Return a 204 No Content status code to indicate successful deletion
    return {"message": "Book deleted successfully"}


# Update route for a book by ID
@app.put("/{book_id}", response_model=BookResponse)
async def update_book(book_id: int, 
                       title: str = None, 
                       description: str = None, 
                       image: UploadFile = File(None), 
                       file: UploadFile = File(None)):
    db = SessionLocal()

    # Find the book by its ID
    book = db.query(Book).filter(Book.id == book_id).first()

    # If book not found, return 404
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # Check if there is an existing image path and if it needs to be deleted
    existing_image_path = book.image
    if image:
        # Check if any other books share the same image path
        if existing_image_path:
            image_usage_count = db.query(func.count(Book.id)).filter(Book.image == existing_image_path).scalar()
            if image_usage_count == 1:  # Only delete if this is the only book using the image
                if os.path.exists(existing_image_path):
                    try:
                        os.remove(existing_image_path)
                    except Exception as e:
                        raise HTTPException(status_code=500, detail=f"Error deleting previous image file: {e}")

        # Save the new image file
        image_path = save_file(image, UPLOAD_FOLDER)
        book.image = image_path

    # Check if there is an existing PDF path and if it needs to be deleted
    existing_pdf_path = book.file
    if file:
        # Check if any other books share the same PDF path
        if existing_pdf_path:
            pdf_usage_count = db.query(func.count(Book.id)).filter(Book.file == existing_pdf_path).scalar()
            if pdf_usage_count == 1:  # Only delete if this is the only book using the PDF
                if os.path.exists(existing_pdf_path):
                    try:
                        os.remove(existing_pdf_path)
                    except Exception as e:
                        raise HTTPException(status_code=500, detail=f"Error deleting previous PDF file: {e}")

        # Save the new PDF file
        new_file_path = save_file(file, UPLOAD_FOLDER)
        book.file = new_file_path

    # Update other book attributes
    if title:
        book.title = title
    if description:
        book.description = description

    # Commit the changes to the database
    db.commit()

    # Return the updated book information
    return {
        "title": book.title,
        "description": book.description,
        "created_at": book.created_at,
        "image": book.image,
        "file": book.file,
        "categories": [category.name for category in book.categories],
        "download_count":book.download_count
    }


@app.post("/{book_id}/download")
async def download_book(book_id: int):
    db = SessionLocal()

    # Find the book by its ID
    book = db.query(Book).filter(Book.id == book_id).first()

    # If book not found, return 404
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # Increment the download count
    book.download_count += 1

    # Create a new download record (optional)
    new_download = Download(book_id=book_id)
    db.add(new_download)

    # Commit changes to the database
    db.commit()

    # Return the file for download (example for a file download)
    file_path = book.file  # Adjust based on how you serve files
    return FileResponse(path=file_path, filename=os.path.basename(file_path))