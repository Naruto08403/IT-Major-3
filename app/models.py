from sqlalchemy import create_engine, Column, Integer, String, Table, ForeignKey,Text,Boolean,DateTime
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, conbytes
from datetime import datetime
from typing import Optional, List
import uuid

# Database setup
DATABASE_URL = "sqlite:///./books.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Association table for many-to-many relationship
book_category_table = Table(
    'book_category', Base.metadata,
    Column('book_id', Integer, ForeignKey('books.id')),
    Column('category_id', Integer, ForeignKey('categories.id'))
)

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

class Download(Base):
    __tablename__ = 'downloads'

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey('books.id'))
    created_at = Column(DateTime, default=datetime.utcnow)

    book = relationship("Book", back_populates="downloads")


# Create the database tables
Base.metadata.create_all(bind=engine)