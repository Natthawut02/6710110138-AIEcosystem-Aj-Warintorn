from fastapi import FastAPI
from app.db.database import engine, Base
from app.routers import auth, users

# Initialize database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="FastAPI Auth & Authorization API",
    description="Authentication & Authorization System with JWT, SQLAlchemy, and Role-Based Access Control",
    version="1.0.0"
)

# Register routers
app.include_router(auth.router)
app.include_router(users.router)


@app.get("/")
def root():
    return {
        "message": "FastAPI Auth API is running!",
        "docs": "/docs",
        "redoc": "/redoc"
    }
