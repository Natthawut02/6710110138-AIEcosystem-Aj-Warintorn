"""
CRUD (Create, Read, Update, Delete) operations for the 'students' table.
"""

from db.database import engine, SessionLocal, Base
from db.models import Student
from sqlalchemy.exc import SQLAlchemyError

def create_students_table():
    """
    Creates the 'students' table in the PostgreSQL database if it does not exist.
    """
    print("[CRUD] Attempting to create 'students' table...")
    try:
        Base.metadata.create_all(bind=engine)
        print("[CRUD] SUCCESS: 'students' table created successfully.")
    except SQLAlchemyError as e:
        print(f"[CRUD] ERROR: Failed to create table: {e}")
    except Exception as e:
        print(f"[CRUD] UNEXPECTED ERROR: {e}")

def insert_student(name: str, age: int, major: str):
    """
    Inserts a new student record into the 'students' table.
    """
    print(f"[CRUD] Attempting to insert student: name={name}, age={age}, major={major}...")
    session = SessionLocal()
    try:
        new_student = Student(name=name, age=age, major=major)
        session.add(new_student)
        session.commit()
        session.refresh(new_student)
        print(f"[CRUD] SUCCESS: Inserted student - ID: {new_student.id}, Name: {new_student.name}, Age: {new_student.age}, Major: {new_student.major}")
        return new_student.id
    except SQLAlchemyError as e:
        session.rollback()
        print(f"[CRUD] ERROR: Failed to insert student: {e}")
        return None
    except Exception as e:
        session.rollback()
        print(f"[CRUD] UNEXPECTED ERROR: {e}")
        return None
    finally:
        session.close()

def update_student(student_id: int, **fields):
    """
    Updates specific fields of an existing student by their ID.
    """
    print(f"[CRUD] Attempting to update student ID {student_id} with fields: {fields}...")
    session = SessionLocal()
    try:
        student = session.query(Student).filter(Student.id == student_id).first()
        if not student:
            print(f"[CRUD] WARNING: Student with ID {student_id} not found.")
            return

        before_str = f"Name: {student.name}, Age: {student.age}, Major: {student.major}"
        
        for key, value in fields.items():
            if hasattr(student, key):
                setattr(student, key, value)
            else:
                print(f"[CRUD] WARNING: Student model has no attribute '{key}'. Skipping.")

        session.commit()
        session.refresh(student)
        after_str = f"Name: {student.name}, Age: {student.age}, Major: {student.major}"
        
        print(f"[CRUD] SUCCESS: Updated student ID {student_id}")
        print(f"  Before: {before_str}")
        print(f"  After : {after_str}")
    except SQLAlchemyError as e:
        session.rollback()
        print(f"[CRUD] ERROR: Failed to update student: {e}")
    except Exception as e:
        session.rollback()
        print(f"[CRUD] UNEXPECTED ERROR: {e}")
    finally:
        session.close()

def delete_student(student_id: int):
    """
    Deletes a student record by their ID.
    """
    print(f"[CRUD] Attempting to delete student ID {student_id}...")
    session = SessionLocal()
    try:
        student = session.query(Student).filter(Student.id == student_id).first()
        if not student:
            print(f"[CRUD] WARNING: Student with ID {student_id} not found.")
            return

        session.delete(student)
        session.commit()
        print(f"[CRUD] SUCCESS: Student ID {student_id} (Name: {student.name}) has been deleted.")
    except SQLAlchemyError as e:
        session.rollback()
        print(f"[CRUD] ERROR: Failed to delete student: {e}")
    except Exception as e:
        session.rollback()
        print(f"[CRUD] UNEXPECTED ERROR: {e}")
    finally:
        session.close()

def drop_students_table():
    """
    Drops the 'students' table from the database.
    """
    print("[CRUD] Attempting to drop 'students' table...")
    try:
        Base.metadata.drop_all(bind=engine)
        print("[CRUD] SUCCESS: 'students' table dropped successfully.")
    except SQLAlchemyError as e:
        print(f"[CRUD] ERROR: Failed to drop table: {e}")
    except Exception as e:
        print(f"[CRUD] UNEXPECTED ERROR: {e}")

def get_all_students():
    """
    Queries and prints all records from the 'students' table.
    """
    print("[CRUD] Querying all students...")
    session = SessionLocal()
    try:
        students = session.query(Student).all()
        if not students:
            print("[CRUD] No student records found in the database.")
            return []
        print(f"[CRUD] SUCCESS: Found {len(students)} student(s):")
        for s in students:
            print(f"  - ID: {s.id}, Name: {s.name}, Age: {s.age}, Major: {s.major}")
        return students
    except SQLAlchemyError as e:
        print(f"[CRUD] ERROR: Failed to query students: {e}")
        return []
    except Exception as e:
        print(f"[CRUD] UNEXPECTED ERROR: {e}")
        return []
    finally:
        session.close()

