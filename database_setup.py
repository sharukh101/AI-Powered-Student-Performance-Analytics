import sqlite3
import pandas as pd
from data_generator import generate_student_data

def setup_database():
    print("Generating student data...")
    df = generate_student_data(1000)
    
    # Split into normalized tables
    # 1. Students table (demographics/habits)
    students_df = df[['student_id', 'name', 'sleep_hours_daily', 'screen_time_daily']]
    
    # 2. Academic performance table
    academic_df = df[['student_id', 'attendance_rate', 'study_hours_weekly', 
                      'assignment_completion_rate', 'midterm_score', 'final_score', 'passed']]
    
    # Connect to SQLite database
    db_name = "student_performance.db"
    print(f"Connecting to database '{db_name}'...")
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    # Create tables
    print("Creating tables...")
    cursor.execute("""
    DROP TABLE IF EXISTS academic_performance;
    """)
    cursor.execute("""
    DROP TABLE IF EXISTS students;
    """)
    
    cursor.execute("""
    CREATE TABLE students (
        student_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        sleep_hours_daily REAL,
        screen_time_daily REAL
    );
    """)
    
    cursor.execute("""
    CREATE TABLE academic_performance (
        student_id TEXT PRIMARY KEY,
        attendance_rate REAL NOT NULL,
        study_hours_weekly REAL NOT NULL,
        assignment_completion_rate REAL NOT NULL,
        midterm_score REAL NOT NULL,
        final_score REAL NOT NULL,
        passed INTEGER NOT NULL CHECK (passed IN (0, 1)),
        FOREIGN KEY (student_id) REFERENCES students (student_id) ON DELETE CASCADE
    );
    """)
    
    # Insert data
    print("Inserting data into 'students' table...")
    students_df.to_sql('students', conn, if_exists='append', index=False)
    
    print("Inserting data into 'academic_performance' table...")
    academic_df.to_sql('academic_performance', conn, if_exists='append', index=False)
    
    conn.commit()
    
    # Verification query
    print("\nDatabase Setup Complete! Verification Summary:")
    cursor.execute("SELECT COUNT(*) FROM students;")
    num_students = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM academic_performance;")
    num_academic = cursor.fetchone()[0]
    
    print(f"Total students in 'students' table: {num_students}")
    print(f"Total academic records: {num_academic}")
    
    # Fetch a sample join query
    cursor.execute("""
        SELECT s.student_id, s.name, a.attendance_rate, a.study_hours_weekly, a.final_score, a.passed
        FROM students s
        JOIN academic_performance a ON s.student_id = a.student_id
        LIMIT 5;
    """)
    rows = cursor.fetchall()
    print("\nSample records:")
    for row in rows:
        print(f"ID: {row[0]} | Name: {row[1]} | Attendance: {row[2]}% | Study Hours: {row[3]} | Final Score: {row[4]} | Passed: {row[5]}")
        
    conn.close()

if __name__ == "__main__":
    setup_database()
