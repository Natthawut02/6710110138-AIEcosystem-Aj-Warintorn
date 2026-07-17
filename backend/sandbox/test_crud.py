import sys
import os

# Add the backend/ directory to the system path to allow importing core modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.crud import (
    create_students_table,
    insert_student,
    get_all_students,
    update_student,
    delete_student,
    drop_students_table,
)

def run_test():
    print("=" * 60)
    print("  STARTING DATABASE CRUD WORKFLOW TEST")
    print("=" * 60)

    # 1. Create Table
    print("\n=== STEP 1: Create Table ===")
    create_students_table()

    # 2. Insert Students
    print("\n=== STEP 2: Insert Students ===")
    id_somchai = insert_student("Somchai", 20, "Computer Engineering")
    id_somying = insert_student("Somying", 21, "Information Technology")
    
    print(f"Captured IDs - Somchai ID: {id_somchai}, Somying ID: {id_somying}")

    # 3. View all students after insertion
    print("\n=== STEP 3: Get All Students (After Insert) ===")
    get_all_students()

    # 4. Update the first student
    print("\n=== STEP 4: Update Student (Somchai) ===")
    if id_somchai is not None:
        update_student(id_somchai, age=22, major="Software Engineering")
    else:
        print("ERROR: Somchai ID is None, skipping update.")

    # 5. View all students after update
    print("\n=== STEP 5: Get All Students (After Update) ===")
    get_all_students()

    # 6. Delete the second student
    print("\n=== STEP 6: Delete Student (Somying) ===")
    if id_somying is not None:
        delete_student(id_somying)
    else:
        print("ERROR: Somying ID is None, skipping delete.")

    # 7. View all students after delete (should only have 1 student)
    print("\n=== STEP 7: Get All Students (After Delete) ===")
    get_all_students()

    # 8. Drop Table
    print("\n=== STEP 8: Drop Table ===")
    drop_students_table()

    print("\n" + "=" * 60)
    print("  DATABASE CRUD WORKFLOW TEST COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    run_test()
