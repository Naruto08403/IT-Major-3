from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from .database import Base, engine
from .routers import books#, categories, users, downloads

# Create tables
# Base.metadata.create_all(bind=engine)

app = FastAPI()

# Include routers
app.include_router(books.app)
# app.include_router(categories.router)
# app.include_router(users.router)
# app.include_router(downloads.router)

@app.get("/")
def read_root():
    return RedirectResponse('/docs')# {"message": "Welcome to digitalShelves API"}
