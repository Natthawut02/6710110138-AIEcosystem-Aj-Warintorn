"""
Database connection and session configuration using SQLAlchemy.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from core.config import settings

# 1. Construct the connection string using settings from core.config
SQLALCHEMY_DATABASE_URL = (
    f"postgresql+psycopg2://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
    f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
)

# 2. Create the SQLAlchemy engine
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# 3. Create a sessionmaker instance
SessionLocal = sessionmaker(bind=engine)

# 4. Create a declarative Base class for models
Base = declarative_base()
