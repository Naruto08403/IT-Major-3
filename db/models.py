from sqlalchemy import create_engine, Column, Integer, String, Table, ForeignKey
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, conbytes
from datetime import datetime
from typing import Optional, List

Base = declarative_base()

# Association table for many-to-many relationship
book_category_table = Table('book_category', Base.metadata,
    Column('book_id', Integer, ForeignKey('books.id'), primary_key=True),
    Column('category_id', Integer, ForeignKey('categories.id'), primary_key=True)
)

class Book(Base):
    __tablename__ = 'books'
    
    id = Column(Integer, primary_key=True)
    title = Column(String)
    author = Column(String)
    description = Column(String, nullable=True)
    published_date = Column(String, nullable=True)
    image = Column(String)  # Store image as a file path or URL
    file = Column(String)  # Store file as a file path or URL
    
    # Relationship to categories
    categories = relationship('Category', secondary=book_category_table, back_populates='books')

class Category(Base):
    __tablename__ = 'categories'
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    
    # Relationship to books
    books = relationship('Book', secondary=book_category_table, back_populates='categories')

# Create an SQLite database and tables
engine = create_engine('sqlite:///library.db')
Base.metadata.create_all(engine)

# Create a session
Session = sessionmaker(bind=engine)
session = Session()
