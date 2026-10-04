from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3

app = FastAPI(
    title="Campus Parcel Management - Student Service",
    description="Microservice for managing student information",
    version="1.0.0"
)

DATABASE = "student.db"


# -----------------------------
# Database Connection
# -----------------------------

def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


# -----------------------------
# Create Database Table
# -----------------------------

def create_table():
    connection = get_db_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            department TEXT NOT NULL,
            year INTEGER NOT NULL
        )
    """)

    connection.commit()
    connection.close()


create_table()


# -----------------------------
# Student Request Model
# -----------------------------

class StudentCreate(BaseModel):
    name: str
    email: str
    department: str
    year: int


# -----------------------------
# Root Endpoint
# -----------------------------

@app.get("/")
def home():
    return {
        "service": "Student Service",
        "status": "running"
    }


# -----------------------------
# Create Student
# -----------------------------

@app.post("/students")
def create_student(student: StudentCreate):

    connection = get_db_connection()

    try:
        cursor = connection.execute(
            """
            INSERT INTO students
            (name, email, department, year)
            VALUES (?, ?, ?, ?)
            """,
            (
                student.name,
                student.email,
                student.department,
                student.year
            )
        )

        connection.commit()

        student_id = cursor.lastrowid

    except sqlite3.IntegrityError:
        connection.close()

        raise HTTPException(
            status_code=400,
            detail="Email already exists"
        )

    connection.close()

    return {
        "message": "Student created successfully",
        "student_id": student_id,
        "name": student.name,
        "email": student.email,
        "department": student.department,
        "year": student.year
    }


# -----------------------------
# Get All Students
# -----------------------------

@app.get("/students")
def get_students():

    connection = get_db_connection()

    rows = connection.execute(
        "SELECT * FROM students ORDER BY id"
    ).fetchall()

    connection.close()

    return [dict(row) for row in rows]


# -----------------------------
# Get One Student
# -----------------------------

@app.get("/students/{student_id}")
def get_student(student_id: int):

    connection = get_db_connection()

    row = connection.execute(
        "SELECT * FROM students WHERE id = ?",
        (student_id,)
    ).fetchone()

    connection.close()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    return dict(row)


# -----------------------------
# Update Student
# -----------------------------

@app.put("/students/{student_id}")
def update_student(
    student_id: int,
    student: StudentCreate
):

    connection = get_db_connection()

    existing_student = connection.execute(
        "SELECT * FROM students WHERE id = ?",
        (student_id,)
    ).fetchone()

    if existing_student is None:
        connection.close()

        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    try:
        connection.execute(
            """
            UPDATE students
            SET name = ?,
                email = ?,
                department = ?,
                year = ?
            WHERE id = ?
            """,
            (
                student.name,
                student.email,
                student.department,
                student.year,
                student_id
            )
        )

        connection.commit()

    except sqlite3.IntegrityError:
        connection.close()

        raise HTTPException(
            status_code=400,
            detail="Email already exists"
        )

    connection.close()

    return {
        "message": "Student updated successfully",
        "student_id": student_id
    }


# -----------------------------
# Delete Student
# -----------------------------

@app.delete("/students/{student_id}")
def delete_student(student_id: int):

    connection = get_db_connection()

    existing_student = connection.execute(
        "SELECT * FROM students WHERE id = ?",
        (student_id,)
    ).fetchone()

    if existing_student is None:
        connection.close()

        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    connection.execute(
        "DELETE FROM students WHERE id = ?",
        (student_id,)
    )

    connection.commit()
    connection.close()

    return {
        "message": "Student deleted successfully",
        "student_id": student_id
    }