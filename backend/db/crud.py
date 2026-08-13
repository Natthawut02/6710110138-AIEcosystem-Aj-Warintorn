"""
CRUD (Create, Read, Update, Delete) operations for the 'students' table.
Supports both standalone script usage and FastAPI dependency injection (db: Session).
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from db.database import engine, SessionLocal, Base
from db.models import Student
from core.logger import get_logger

logger = get_logger(__name__)


def create_students_table():
    """
    Creates the 'students' table in the PostgreSQL database if it does not exist.
    """
    logger.info("Attempting to create 'students' table...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("SUCCESS: 'students' table created successfully.")
    except SQLAlchemyError as e:
        logger.error(f"Failed to create table: {e}")
        raise
    except Exception as e:
        logger.critical(f"Unexpected error while creating table: {e}")
        raise


def drop_students_table():
    """
    Drops the 'students' table from the database.
    """
    logger.warning("Attempting to drop 'students' table...")
    try:
        Base.metadata.drop_all(bind=engine)
        logger.info("SUCCESS: 'students' table dropped successfully.")
    except SQLAlchemyError as e:
        logger.error(f"Failed to drop table: {e}")
        raise


def get_all_students(skip: int = 0, limit: int = 100, db: Optional[Session] = None) -> List[Student]:
    """
    Queries and returns paginated student records from the database.
    """
    owns_session = False
    if db is None:
        db = SessionLocal()
        owns_session = True

    try:
        students = db.query(Student).offset(skip).limit(limit).all()
        logger.debug(f"Retrieved {len(students)} student record(s) from database.")
        return students
    except SQLAlchemyError as e:
        logger.error(f"Database error while querying students: {e}")
        return []
    finally:
        if owns_session:
            db.close()


def get_student_by_id(student_id: int, db: Optional[Session] = None) -> Optional[Student]:
    """
    Finds a single student by primary key ID.
    """
    owns_session = False
    if db is None:
        db = SessionLocal()
        owns_session = True

    try:
        student = db.query(Student).filter(Student.id == student_id).first()
        return student
    except SQLAlchemyError as e:
        logger.error(f"Database error while finding student ID {student_id}: {e}")
        return None
    finally:
        if owns_session:
            db.close()


def insert_student(name: str, age: Optional[int] = None, major: Optional[str] = None, db: Optional[Session] = None) -> Optional[Student]:
    """
    Inserts a new student record into the 'students' table.
    """
    logger.info(f"Attempting to insert student: name='{name}', age={age}, major='{major}'")
    owns_session = False
    if db is None:
        db = SessionLocal()
        owns_session = True

    try:
        new_student = Student(name=name, age=age, major=major)
        db.add(new_student)
        db.commit()
        db.refresh(new_student)
        logger.info(f"SUCCESS: Inserted student ID {new_student.id} ('{new_student.name}')")
        return new_student
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Failed to insert student: {e}")
        return None
    finally:
        if owns_session:
            db.close()


def update_student(student_id: int, db: Optional[Session] = None, **fields) -> Optional[Student]:
    """
    Updates specific fields of an existing student by their ID.
    """
    logger.info(f"Attempting to update student ID {student_id} with fields: {fields}")
    owns_session = False
    if db is None:
        db = SessionLocal()
        owns_session = True

    try:
        student = db.query(Student).filter(Student.id == student_id).first()
        if not student:
            logger.warning(f"Student with ID {student_id} not found.")
            return None

        for key, value in fields.items():
            if hasattr(student, key) and value is not None:
                setattr(student, key, value)

        db.commit()
        db.refresh(student)
        logger.info(f"SUCCESS: Updated student ID {student_id}")
        return student
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Failed to update student ID {student_id}: {e}")
        return None
    finally:
        if owns_session:
            db.close()


def delete_student(student_id: int, db: Optional[Session] = None) -> bool:
    """
    Deletes a student record by their ID.
    """
    logger.info(f"Attempting to delete student ID {student_id}")
    owns_session = False
    if db is None:
        db = SessionLocal()
        owns_session = True

    try:
        student = db.query(Student).filter(Student.id == student_id).first()
        if not student:
            logger.warning(f"Student with ID {student_id} not found.")
            return False

        db.delete(student)
        db.commit()
        logger.info(f"SUCCESS: Student ID {student_id} ({student.name}) deleted.")
        return True
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Failed to delete student ID {student_id}: {e}")
        return False
    finally:
        if owns_session:
            db.close()
