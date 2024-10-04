from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Query
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Text, DateTime, Table, ForeignKey
from sqlalchemy.orm import relationship, declarative_base, sessionmaker
from sqlalchemy import create_engine
from datetime import datetime
import os
import shutil
from sqlalchemy import func  # Add this import
# FastAPI app setup
app = FastAPI()

# Database setup
DATABASE_URL = "sqlite:///./books.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Upload folder
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Association table for many-to-many relationship
book_category_table = Table(
    'book_category', Base.metadata,
    Column('book_id', Integer, ForeignKey('books.id')),
    Column('category_id', Integer, ForeignKey('categories.id'))
)
class Download(Base):
    __tablename__ = 'downloads'

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey('books.id'))
    created_at = Column(DateTime, default=datetime.utcnow)

    book = relationship("Book", back_populates="downloads")

# Book model
class Book(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    image = Column(String(200), nullable=True)  # Path to the image file
    file = Column(String(200), nullable=True)   # Path to the PDF file
    categories = relationship('Category', secondary=book_category_table, back_populates='books')
    download_count = Column(Integer, default=0)  # Add this field
    # Relationship to Downloads
    downloads = relationship("Download", back_populates="book", cascade="all, delete-orphan")

# Category model
class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    books = relationship('Book', secondary=book_category_table, back_populates='categories')

# Create the database tables
Base.metadata.create_all(bind=engine)

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

# Pydantic schema for Category response
class CategoryResponse(BaseModel):
    name: str

    class Config:
        orm_mode = True

# Helper function to save files
def save_file(file: UploadFile, folder: str):
    file_location = os.path.join(folder, file.filename)
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return file_location

# Route to add a book with multiple categories
@app.post("/books", response_class=JSONResponse)
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
@app.get("/books", response_model=list[BookResponse])
async def get_books():
    db = SessionLocal()
    books = db.query(Book).all()
    return books

# Route to get all categories
@app.get("/categories", response_model=list[CategoryResponse])
async def get_categories():
    db = SessionLocal()
    categories = db.query(Category).all()
    return categories

# New Route to get books based on a given category
@app.get("/books/by-category", response_model=list[BookResponse])
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
from sqlalchemy import func
from fastapi import FastAPI, HTTPException, status
import os

# Delete route for a book by ID
@app.delete("/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
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
@app.put("/books/{book_id}", response_model=BookResponse)
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


@app.post("/books/{book_id}/download")
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

