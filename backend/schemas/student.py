"""
Pydantic schemas for Student entity (PostgreSQL CRUD).
"""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class StudentBase(BaseModel):
    """Base student properties shared across request/response schemas."""
    name: str = Field(
        ..., 
        min_length=2, 
        max_length=100, 
        description="Full name of the student", 
        examples=["Somchai Prasert"]
    )
    age: Optional[int] = Field(
        None, 
        ge=1, 
        le=120, 
        description="Age of the student in years", 
        examples=[21]
    )
    major: Optional[str] = Field(
        None, 
        max_length=100, 
        description="Field of study or academic department", 
        examples=["Computer Engineering"]
    )


class StudentCreate(StudentBase):
    """Schema for creating a new student record."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Somchai Prasert",
                "age": 21,
                "major": "Computer Engineering"
            }
        }
    )


class StudentUpdate(BaseModel):
    """Schema for updating an existing student record (all fields optional)."""
    name: Optional[str] = Field(
        None, 
        min_length=2, 
        max_length=100, 
        description="Updated full name of the student", 
        examples=["Somchai Prasert (Updated)"]
    )
    age: Optional[int] = Field(
        None, 
        ge=1, 
        le=120, 
        description="Updated age of the student", 
        examples=[22]
    )
    major: Optional[str] = Field(
        None, 
        max_length=100, 
        description="Updated academic department", 
        examples=["Artificial Intelligence"]
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "age": 22,
                "major": "Artificial Intelligence"
            }
        }
    )


class StudentResponse(StudentBase):
    """Schema for student data returned from API."""
    id: int = Field(..., description="Unique database identifier (Primary Key)", examples=[1])

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "name": "Somchai Prasert",
                "age": 21,
                "major": "Computer Engineering"
            }
        }
    )
