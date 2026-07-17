"""
SQLAlchemy ORM models.
"""

from sqlalchemy import Column, Integer, String
from db.database import Base

class Student(Base):
    """
    Student model representing the 'students' table in the database.
    """
    __tablename__ = "students"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    age = Column(Integer)
    major = Column(String)
