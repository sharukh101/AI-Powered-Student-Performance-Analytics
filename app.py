from flask import Flask, render_template, jsonify, request
import sqlite3
import joblib
import pandas as pd
import numpy as np
import os

app = Flask(__name__)

DB_NAME = "student_performance.db"

# Helper to check if database exists
def db_exists():
    return os.path.exists(DB_NAME)

# Helper to run read-only queries
def query_db(query, args=(), one=False):
    if not db_exists():
        return []
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(query, args)
    rv = cur.fetchall()
    conn.close()
    return (rv[0] if rv else None) if one else rv

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/stats')
def get_stats():
    if not db_exists():
        return jsonify({"error": "Database not initialized. Please run setup first."}), 400
        
    # Cohort stats
    cohort_stats = query_db("""
        SELECT 
            COUNT(*) AS total_students,
            ROUND(AVG(a.attendance_rate), 1) AS avg_attendance_rate,
            ROUND(AVG(a.study_hours_weekly), 1) AS avg_study_hours,
            ROUND(100.0 * SUM(a.passed) / COUNT(*), 1) AS passing_rate
        FROM academic_performance a;
    """, one=True)
    
    # Risk breakdown
    risk_stats = query_db("""
        SELECT risk_level, COUNT(*) as count
        FROM performance_predictions
        GROUP BY risk_level
    """)
    
    risk_dict = {row['risk_level']: row['count'] for row in risk_stats}
    
    return jsonify({
        "total_students": cohort_stats['total_students'],
        "avg_attendance_rate": cohort_stats['avg_attendance_rate'],
        "avg_study_hours": cohort_stats['avg_study_hours'],
        "passing_rate": cohort_stats['passing_rate'],
        "risk_breakdown": {
            "High": risk_dict.get("High", 0),
            "Medium": risk_dict.get("Medium", 0),
            "Low": risk_dict.get("Low", 0)
        }
    })

@app.route('/api/charts')
def get_chart_data():
    if not db_exists():
        return jsonify({"error": "Database not initialized"}), 400
        
    # Scatter plot: Attendance vs Final Score (limit to 200 points to keep UI fast & clean)
    scatter_data = query_db("""
        SELECT attendance_rate, final_score 
        FROM academic_performance 
        ORDER BY RANDOM() 
        LIMIT 200
    """)
    scatter_list = [{"x": row['attendance_rate'], "y": row['final_score']} for row in scatter_data]
    
    # Study hours distribution/impact
    study_data = query_db("""
        SELECT 
            ROUND(study_hours_weekly) as hours,
            ROUND(AVG(final_score), 1) as avg_score
        FROM academic_performance
        GROUP BY hours
        ORDER BY hours ASC
    """)
    study_list = [{"x": row['hours'], "y": row['avg_score']} for row in study_data]
    
    return jsonify({
        "scatter": scatter_list,
        "study_hours_impact": study_list
    })

@app.route('/api/predict', methods=['POST'])
def predict():
    try:
        # Load ML models
        if not os.path.exists('final_score_model.joblib') or not os.path.exists('pass_model.joblib'):
            return jsonify({"error": "ML models not trained. Please run training pipeline first."}), 400
            
        reg_model = joblib.load('final_score_model.joblib')
        clf_model = joblib.load('pass_model.joblib')
        
        data = request.json
        attendance_rate = float(data.get('attendance_rate', 85))
        study_hours_weekly = float(data.get('study_hours_weekly', 12))
        sleep_hours_daily = float(data.get('sleep_hours_daily', 7))
        screen_time_daily = float(data.get('screen_time_daily', 4))
        assignment_completion_rate = float(data.get('assignment_completion_rate', 80))
        midterm_score = float(data.get('midterm_score', 75))
        
        # Prepare feature vector
        features = [[
            attendance_rate,
            study_hours_weekly,
            sleep_hours_daily,
            screen_time_daily,
            assignment_completion_rate,
            midterm_score
        ]]
        
        # Predict Final Score
        pred_score = reg_model.predict(features)[0]
        
        # Predict Pass Probability
        pass_prob = clf_model.predict_proba(features)[0][1]
        
        # Determine risk level
        fail_prob = 1.0 - pass_prob
        if fail_prob >= 0.55:
            risk = "High"
        elif fail_prob >= 0.20:
            risk = "Medium"
        else:
            risk = "Low"
            
        return jsonify({
            "predicted_final_score": round(float(pred_score), 1),
            "pass_probability": round(float(pass_prob * 100), 1),
            "risk_level": risk
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/run-sql', methods=['POST'])
def run_sql():
    if not db_exists():
        return jsonify({"error": "Database not initialized"}), 400
        
    data = request.json
    sql_type = data.get('query_type')
    
    queries = {
        "attendance_impact": """
            SELECT 
                CASE 
                    WHEN attendance_rate < 70 THEN 'Low (< 70%)'
                    WHEN attendance_rate >= 70 AND attendance_rate < 85 THEN 'Medium (70% - 85%)'
                    ELSE 'High (>= 85%)'
                END AS attendance_band,
                COUNT(*) AS student_count,
                ROUND(AVG(study_hours_weekly), 1) AS avg_study_hours,
                ROUND(AVG(final_score), 1) AS avg_final_score,
                ROUND(100.0 * SUM(passed) / COUNT(*), 1) AS passing_rate
            FROM academic_performance
            GROUP BY attendance_band
            ORDER BY avg_final_score DESC;
        """,
        "study_hours_impact": """
            SELECT 
                CASE 
                    WHEN study_hours_weekly < 5 THEN 'Low (< 5 hrs/wk)'
                    WHEN study_hours_weekly >= 5 AND study_hours_weekly < 15 THEN 'Moderate (5-15 hrs/wk)'
                    ELSE 'High (>= 15 hrs/wk)'
                END AS study_hours_band,
                COUNT(*) AS student_count,
                ROUND(AVG(attendance_rate), 1) AS avg_attendance,
                ROUND(AVG(final_score), 1) AS avg_final_score,
                ROUND(100.0 * SUM(passed) / COUNT(*), 1) AS passing_rate
            FROM academic_performance
            GROUP BY study_hours_band
            ORDER BY avg_final_score DESC;
        """,
        "high_risk_students": """
            SELECT 
                s.student_id,
                s.name,
                a.attendance_rate || '%' as attendance,
                a.midterm_score || '/100' as midterm,
                a.study_hours_weekly || ' hrs' as study_hours
            FROM students s
            JOIN academic_performance a ON s.student_id = a.student_id
            WHERE a.attendance_rate < 75.0 AND a.midterm_score < 50.0
            ORDER BY a.attendance_rate ASC, a.midterm_score ASC
            LIMIT 10;
        """,
        "sleep_screen_impact": """
            SELECT 
                CASE WHEN a.passed = 1 THEN 'Passing Students' ELSE 'Failing Students' END AS group_name,
                COUNT(*) AS student_count,
                ROUND(AVG(s.sleep_hours_daily), 1) AS avg_sleep_hours,
                ROUND(AVG(s.screen_time_daily), 1) AS avg_screen_time,
                ROUND(AVG(a.final_score), 1) AS avg_final_score
            FROM students s
            JOIN academic_performance a ON s.student_id = a.student_id
            GROUP BY a.passed;
        """
    }
    
    query = queries.get(sql_type)
    if not query:
        return jsonify({"error": "Invalid query selection"}), 400
        
    try:
        conn = sqlite3.connect(DB_NAME)
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        # Format output as table
        columns = list(df.columns)
        records = df.to_dict(orient='records')
        
        return jsonify({
            "columns": columns,
            "records": records,
            "raw_sql": query.strip()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    import webbrowser
    from threading import Timer

    def open_browser():
        webbrowser.open("http://127.0.0.1:5000")

    # Open browser automatically on startup (only once, handling Werkzeug reloader, and only if not running on Render)
    if not os.environ.get("RENDER"):
        if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
            Timer(1.2, open_browser).start()
        elif not app.debug:
            Timer(1.2, open_browser).start()

    app.run(debug=True, port=5000)
