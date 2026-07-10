-- AI-Powered Student Performance Analytics: Analysis SQL Queries

-- 1. General Cohort Statistics
-- Returns total students, average attendance, average weekly study hours, and overall passing rate.
SELECT 
    COUNT(*) AS total_students,
    ROUND(AVG(a.attendance_rate), 2) AS avg_attendance_rate,
    ROUND(AVG(a.study_hours_weekly), 2) AS avg_study_hours_weekly,
    ROUND(100.0 * SUM(a.passed) / COUNT(*), 2) AS passing_percentage
FROM academic_performance a;


-- 2. Impact of Attendance on Performance
-- Groups students by attendance bands and checks average final score and passing percentage.
SELECT 
    CASE 
        WHEN attendance_rate < 70 THEN 'Low Attendance (< 70%)'
        WHEN attendance_rate >= 70 AND attendance_rate < 85 THEN 'Medium Attendance (70% - 85%)'
        ELSE 'High Attendance (>= 85%)'
    END AS attendance_band,
    COUNT(*) AS student_count,
    ROUND(AVG(study_hours_weekly), 2) AS avg_study_hours,
    ROUND(AVG(final_score), 2) AS avg_final_score,
    ROUND(100.0 * SUM(passed) / COUNT(*), 2) AS passing_percentage
FROM academic_performance
GROUP BY attendance_band
ORDER BY avg_final_score DESC;


-- 3. Impact of Weekly Study Hours on Performance
-- Groups students by weekly study hours and checks final scores and passing percentage.
SELECT 
    CASE 
        WHEN study_hours_weekly < 5 THEN 'Low Study Hours (<5 hrs/wk)'
        WHEN study_hours_weekly >= 5 AND study_hours_weekly < 15 THEN 'Moderate Study Hours (5-15 hrs/wk)'
        ELSE 'High Study Hours (>=15 hrs/wk)'
    END AS study_hours_band,
    COUNT(*) AS student_count,
    ROUND(AVG(attendance_rate), 2) AS avg_attendance,
    ROUND(AVG(final_score), 2) AS avg_final_score,
    ROUND(100.0 * SUM(passed) / COUNT(*), 2) AS passing_percentage
FROM academic_performance
GROUP BY study_hours_band
ORDER BY avg_final_score DESC;


-- 4. High Risk Students Identification
-- Lists students with attendance under 75% AND midterm scores under 50.
-- These students represent candidates for immediate academic intervention.
SELECT 
    s.student_id,
    s.name,
    a.attendance_rate,
    a.midterm_score,
    a.study_hours_weekly
FROM students s
JOIN academic_performance a ON s.student_id = a.student_id
WHERE a.attendance_rate < 75.0 AND a.midterm_score < 50.0
ORDER BY a.attendance_rate ASC, a.midterm_score ASC;


-- 5. Comparison of Sleep and Screen Time on Passing Rates
-- Analyzes whether lifestyle variables show correlations with academic outcome.
SELECT 
    a.passed,
    COUNT(*) AS student_count,
    ROUND(AVG(s.sleep_hours_daily), 2) AS avg_sleep_hours,
    ROUND(AVG(s.screen_time_daily), 2) AS avg_screen_time,
    ROUND(AVG(a.attendance_rate), 2) AS avg_attendance,
    ROUND(AVG(a.final_score), 2) AS avg_final_score
FROM students s
JOIN academic_performance a ON s.student_id = a.student_id
GROUP BY a.passed;
