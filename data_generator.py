import pandas as pd
import numpy as np
import random

def generate_student_data(num_students=1000, seed=42):
    np.random.seed(seed)
    random.seed(seed)
    
    first_names = [
        "Aarav", "Aditi", "Amit", "Ananya", "Arjun", "Deepak", "Divya", "Ishaan", "Kavya", "Manish",
        "Neha", "Pranav", "Pooja", "Rahul", "Riya", "Rohan", "Sanjana", "Saurabh", "Sneha", "Vikram",
        "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", "William", "Elizabeth",
        "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen"
    ]
    
    last_names = [
        "Sharma", "Verma", "Gupta", "Mehta", "Singh", "Joshi", "Patel", "Rao", "Nair", "Kumar",
        "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
        "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin"
    ]
    
    student_ids = [f"STU{i:04d}" for i in range(1, num_students + 1)]
    names = [f"{random.choice(first_names)} {random.choice(last_names)}" for _ in range(num_students)]
    
    # Generate features
    # Attendance rate: mean 84%, std 12%, bounded 40% to 100%
    attendance_rate = np.random.normal(84, 12, num_students)
    attendance_rate = np.clip(attendance_rate, 40, 100).round(1)
    
    # Study hours weekly: mean 12 hours, std 5.5, bounded 1 to 30
    study_hours_weekly = np.random.normal(12, 5.5, num_students)
    study_hours_weekly = np.clip(study_hours_weekly, 1, 30).round(1)
    
    # Sleep hours daily: mean 7, std 1.2, bounded 4 to 10
    sleep_hours_daily = np.random.normal(7, 1.2, num_students)
    sleep_hours_daily = np.clip(sleep_hours_daily, 4, 10).round(1)
    
    # Screen time daily: mean 4.5, std 1.8, bounded 1 to 12
    screen_time_daily = np.random.normal(4.5, 1.8, num_students)
    screen_time_daily = np.clip(screen_time_daily, 1, 12).round(1)
    
    # Assignment completion rate: correlated with attendance and study hours
    assignment_completion_base = 0.5 * attendance_rate + 1.5 * study_hours_weekly
    assignment_completion_noise = np.random.normal(20, 10, num_students)
    assignment_completion_rate = assignment_completion_base + assignment_completion_noise
    assignment_completion_rate = np.clip(assignment_completion_rate, 10, 100).round(1)
    
    # Midterm score: correlated with attendance and study hours
    midterm_base = 25 + 0.4 * attendance_rate + 1.2 * study_hours_weekly
    midterm_noise = np.random.normal(0, 8, num_students)
    midterm_score = midterm_base + midterm_noise
    midterm_score = np.clip(midterm_score, 20, 100).round(1)
    
    # Final exam score: highly correlated with midterm, study hours, attendance, and assignment completion
    final_score_base = (
        0.45 * midterm_score + 
        0.25 * attendance_rate + 
        0.9 * study_hours_weekly + 
        0.15 * assignment_completion_rate
    )
    final_score_noise = np.random.normal(0, 6, num_students)
    final_score = final_score_base + final_score_noise
    # Make sure we don't exceed 100
    final_score = np.clip(final_score, 10, 100).round(1)
    
    # Passed binary label
    passed = (final_score >= 50).astype(int)
    
    # Combine into DataFrame
    df = pd.DataFrame({
        'student_id': student_ids,
        'name': names,
        'attendance_rate': attendance_rate,
        'study_hours_weekly': study_hours_weekly,
        'sleep_hours_daily': sleep_hours_daily,
        'screen_time_daily': screen_time_daily,
        'assignment_completion_rate': assignment_completion_rate,
        'midterm_score': midterm_score,
        'final_score': final_score,
        'passed': passed
    })
    
    return df

if __name__ == "__main__":
    df = generate_student_data(1000)
    df.to_csv("students_data.csv", index=False)
    print(f"Successfully generated {len(df)} student records and saved to students_data.csv")
    print(df.head())
