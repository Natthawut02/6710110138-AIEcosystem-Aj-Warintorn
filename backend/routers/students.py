"""
Student Database Management Endpoints (PostgreSQL + SQLAlchemy).
Provides full CRUD capabilities for student records.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.orm import Session
from db.database import get_db
from db import crud
from schemas.student import StudentCreate, StudentUpdate, StudentResponse
from schemas.common import StandardResponse, ErrorResponse

router = APIRouter(
    prefix="/students",
    tags=["Student Management"]
)


@router.post(
    "",
    response_model=StudentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a New Student Record",
    description="""
Persists a new student record into the PostgreSQL database.

- **name**: Full student name (required, 2-100 characters).
- **age**: Student age in years (optional, 1-120).
- **major**: Academic major / department (optional).
    """,
    response_description="The newly created student record including generated ID",
    responses={
        201: {"description": "Student created successfully", "model": StudentResponse},
        400: {"description": "Validation error or invalid input payload", "model": ErrorResponse},
        500: {"description": "Database persistence failure", "model": ErrorResponse}
    }
)
def create_student(student_in: StudentCreate, db: Session = Depends(get_db)):
    """Create a new student entry in PostgreSQL."""
    student = crud.insert_student(
        name=student_in.name,
        age=student_in.age,
        major=student_in.major,
        db=db
    )
    if not student:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save student record to database."
        )
    return student


@router.get(
    "",
    response_model=List[StudentResponse],
    status_code=status.HTTP_200_OK,
    summary="List All Students",
    description="""
Retrieves a paginated list of student records from PostgreSQL.
Supports offset pagination via `skip` and `limit` query parameters.
    """,
    response_description="List of student records",
    responses={
        200: {"description": "List of students retrieved successfully", "model": List[StudentResponse]}
    }
)
def list_students(
    skip: int = Query(0, ge=0, description="Number of records to skip (offset)", examples=[0]),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of records to return", examples=[20]),
    db: Session = Depends(get_db)
):
    """Retrieve all student entries with pagination."""
    return crud.get_all_students(skip=skip, limit=limit, db=db)


@router.get(
    "/{student_id}",
    response_model=StudentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Student by ID",
    description="""
Retrieves the complete profile of a single student using their unique integer ID.
Returns `404 Not Found` if no student exists with the provided ID.
    """,
    response_description="Student details corresponding to the provided ID",
    responses={
        200: {"description": "Student record found", "model": StudentResponse},
        404: {"description": "Student record not found", "model": ErrorResponse}
    }
)
def get_student(
    student_id: int = Path(..., ge=1, description="Primary key ID of the student to fetch", examples=[1]),
    db: Session = Depends(get_db)
):
    """Fetch a single student by primary key ID."""
    student = crud.get_student_by_id(student_id=student_id, db=db)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID {student_id} was not found."
        )
    return student


@router.put(
    "/{student_id}",
    response_model=StudentResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Student Record",
    description="""
Modifies one or more attributes of an existing student record in PostgreSQL.
Only fields included in the request body will be updated.
    """,
    response_description="The updated student record",
    responses={
        200: {"description": "Student record updated successfully", "model": StudentResponse},
        404: {"description": "Student not found for update", "model": ErrorResponse}
    }
)
def update_student(
    student_id: int = Path(..., ge=1, description="ID of the student to update", examples=[1]),
    student_in: StudentUpdate = ...,
    db: Session = Depends(get_db)
):
    """Update fields on an existing student."""
    update_data = student_in.model_dump(exclude_unset=True)
    updated = crud.update_student(student_id=student_id, db=db, **update_data)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID {student_id} not found or could not be updated."
        )
    return updated


@router.delete(
    "/{student_id}",
    response_model=StandardResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Delete Student Record",
    description="""
Deletes a student record permanently from the PostgreSQL database.
    """,
    response_description="Confirmation of successful deletion",
    responses={
        200: {"description": "Student record deleted successfully"},
        404: {"description": "Student not found for deletion", "model": ErrorResponse}
    }
)
def delete_student(
    student_id: int = Path(..., ge=1, description="ID of the student to delete", examples=[1]),
    db: Session = Depends(get_db)
):
    """Delete a student record by ID."""
    success = crud.delete_student(student_id=student_id, db=db)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID {student_id} not found or could not be deleted."
        )
    return StandardResponse(
        success=True,
        message=f"Student ID {student_id} deleted successfully.",
        data={"deleted_id": student_id}
    )
