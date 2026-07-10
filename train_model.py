import sqlite3
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.metrics import mean_absolute_error, r2_score, accuracy_score, classification_report
import joblib

def train_and_save_models():
    # 1. Connect to SQLite database and load data
    db_name = "student_performance.db"
    print(f"Loading data from database: {db_name}...")
    conn = sqlite3.connect(db_name)
    
    query = """
        SELECT s.student_id, s.name, s.sleep_hours_daily, s.screen_time_daily,
               a.attendance_rate, a.study_hours_weekly, a.assignment_completion_rate, 
               a.midterm_score, a.final_score, a.passed
        FROM students s
        JOIN academic_performance a ON s.student_id = a.student_id
    """
    df = pd.read_sql_query(query, conn)
    
    # Define features and targets
    feature_cols = [
        'attendance_rate', 
        'study_hours_weekly', 
        'sleep_hours_daily', 
        'screen_time_daily', 
        'assignment_completion_rate', 
        'midterm_score'
    ]
    
    X = df[feature_cols]
    y_reg = df['final_score']
    y_clf = df['passed']
    
    # 2. Split data
    X_train, X_test, y_reg_train, y_reg_test, y_clf_train, y_clf_test = train_test_split(
        X, y_reg, y_clf, test_size=0.2, random_state=42
    )
    
    # 3. Train Regression Model (Predict Final Score)
    print("Training Final Score Regressor (Random Forest)...")
    reg_model = RandomForestRegressor(n_estimators=100, random_state=42)
    reg_model.fit(X_train, y_reg_train)
    
    # Evaluate Regressor
    reg_preds = reg_model.predict(X_test)
    mae = mean_absolute_error(y_reg_test, reg_preds)
    r2 = r2_score(y_reg_test, reg_preds)
    print(f"Regressor Metrics: MAE = {mae:.2f}, R² Score = {r2:.4f}")
    
    # 4. Train Classification Model (Predict Pass/Fail)
    print("Training Pass/Fail Classifier (Random Forest)...")
    clf_model = RandomForestClassifier(n_estimators=100, random_state=42)
    clf_model.fit(X_train, y_clf_train)
    
    # Evaluate Classifier
    clf_preds = clf_model.predict(X_test)
    accuracy = accuracy_score(y_clf_test, clf_preds)
    print(f"Classifier Metrics: Accuracy = {accuracy:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_clf_test, clf_preds))
    
    # 5. Save Models
    print("Saving models to disk...")
    joblib.dump(reg_model, 'final_score_model.joblib')
    joblib.dump(clf_model, 'pass_model.joblib')
    
    # 6. Generate predictions for ALL students in the database
    print("Generating predictions for the entire cohort...")
    all_reg_preds = reg_model.predict(X)
    # Get probabilities for class 1 (passed)
    all_clf_probs = clf_model.predict_proba(X)[:, 1]
    
    # Determine risk level based on fail probability (1 - pass_probability)
    # High Risk: Pass probability < 45%
    # Medium Risk: Pass probability between 45% and 80%
    # Low Risk: Pass probability >= 80%
    fail_probs = 1 - all_clf_probs
    risk_levels = []
    for fp in fail_probs:
        if fp >= 0.55:
            risk_levels.append('High')
        elif fp >= 0.20:
            risk_levels.append('Medium')
        else:
            risk_levels.append('Low')
            
    predictions_df = pd.DataFrame({
        'student_id': df['student_id'],
        'predicted_final_score': all_reg_preds.round(1),
        'pass_probability': (all_clf_probs * 100).round(1),
        'risk_level': risk_levels
    })
    
    # Write predictions to SQLite database
    print("Writing predictions to database...")
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS performance_predictions;")
    
    cursor.execute("""
        CREATE TABLE performance_predictions (
            student_id TEXT PRIMARY KEY,
            predicted_final_score REAL NOT NULL,
            pass_probability REAL NOT NULL,
            risk_level TEXT NOT NULL,
            FOREIGN KEY (student_id) REFERENCES students (student_id) ON DELETE CASCADE
        );
    """)
    
    predictions_df.to_sql('performance_predictions', conn, if_exists='append', index=False)
    conn.commit()
    
    # 7. Export combined CSV for Power BI
    print("Exporting combined data to CSV for Power BI...")
    combined_df = df.merge(predictions_df, on='student_id')
    combined_df.to_csv("students_predictions_combined.csv", index=False)
    print("Exported students_predictions_combined.csv successfully.")
    
    # Log feature importances
    importances = reg_model.feature_importances_
    for col, imp in zip(feature_cols, importances):
        print(f"Feature '{col}' Importance: {imp:.4f}")
        
    conn.close()
    print("Model pipeline finished successfully!")

if __name__ == "__main__":
    train_and_save_models()
