// EduPredict.ai Client Dashboard Script

let impactChartInstance = null;
let riskChartInstance = null;
let chartDataCache = null;
let activeChartType = 'scatter'; // 'scatter' or 'line'

const sqlQueriesCode = {
    attendance_impact: `-- Attendance Impact Analysis
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
ORDER BY avg_final_score DESC;`,

    study_hours_impact: `-- Study Hours Impact Analysis
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
ORDER BY avg_final_score DESC;`,

    high_risk_students: `-- Top 10 High-Risk Students (For Immediate Intervention)
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
LIMIT 10;`,

    sleep_screen_impact: `-- Correlation of Lifestyle Variables
SELECT 
    CASE WHEN a.passed = 1 THEN 'Passing Students' ELSE 'Failing Students' END AS group_name,
    COUNT(*) AS student_count,
    ROUND(AVG(s.sleep_hours_daily), 1) AS avg_sleep_hours,
    ROUND(AVG(s.screen_time_daily), 1) AS avg_screen_time,
    ROUND(AVG(a.final_score), 1) AS avg_final_score
FROM students s
JOIN academic_performance a ON s.student_id = a.student_id
GROUP BY a.passed;`
};

document.addEventListener("DOMContentLoaded", () => {
    // Initial fetch
    refreshDashboardData();
    setupInputListeners();
    loadSqlQueryText();
});

function refreshDashboardData() {
    fetchStats();
    fetchChartData();
}

// Fetch general stats and populate KPIs
function fetchStats() {
    fetch('/api/stats')
        .then(response => {
            if (!response.ok) throw new Error("Stats not loaded");
            return response.json();
        })
        .then(data => {
            document.getElementById('stat-total-students').innerText = data.total_students.toLocaleString();
            document.getElementById('stat-avg-attendance').innerText = data.avg_attendance_rate + '%';
            document.getElementById('stat-avg-study-hours').innerText = data.avg_study_hours + ' hrs';
            document.getElementById('stat-passing-rate').innerText = data.passing_rate + '%';
            
            renderRiskDistributionChart(data.risk_breakdown);
        })
        .catch(err => {
            console.error("Error loading cohort statistics:", err);
            // Display friendly alert/fallback
        });
}

// Fetch data for both charts
function fetchChartData() {
    fetch('/api/charts')
        .then(response => {
            if (!response.ok) throw new Error("Charts not loaded");
            return response.json();
        })
        .then(data => {
            chartDataCache = data;
            renderImpactChart();
        })
        .catch(err => {
            console.error("Error loading chart data:", err);
        });
}

// Render Risk Distribution Chart (Pie)
function renderRiskDistributionChart(breakdown) {
    const ctx = document.getElementById('riskChart').getContext('2d');
    
    if (riskChartInstance) {
        riskChartInstance.destroy();
    }
    
    riskChartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Low Risk', 'Medium Risk', 'High Risk'],
            datasets: [{
                data: [breakdown.Low, breakdown.Medium, breakdown.High],
                backgroundColor: [
                    'rgba(16, 185, 129, 0.65)',  // Emerald
                    'rgba(245, 158, 11, 0.65)',   // Amber
                    'rgba(239, 68, 68, 0.65)'     // Rose/Red
                ],
                borderColor: [
                    'rgba(16, 185, 129, 1)',
                    'rgba(245, 158, 11, 1)',
                    'rgba(239, 68, 68, 1)'
                ],
                borderWidth: 1.5,
                hoverOffset: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: 'hsl(210, 38%, 95%)',
                        font: { family: 'Inter', size: 11 },
                        padding: 15
                    }
                }
            },
            cutout: '65%'
        }
    });
}

// Render Attendance vs. Performance Impact chart (Scatter or Line)
function renderImpactChart() {
    const ctx = document.getElementById('impactChart').getContext('2d');
    
    if (impactChartInstance) {
        impactChartInstance.destroy();
    }
    
    if (!chartDataCache) return;
    
    if (activeChartType === 'scatter') {
        // Attendance vs Final Score
        impactChartInstance = new Chart(ctx, {
            type: 'scatter',
            data: {
                datasets: [{
                    label: 'Students Correlation',
                    data: chartDataCache.scatter,
                    backgroundColor: 'rgba(0, 242, 254, 0.55)',
                    borderColor: 'rgba(0, 242, 254, 0.85)',
                    borderWidth: 1,
                    pointRadius: 4,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: {
                        title: { display: true, text: 'Attendance Rate (%)', color: 'hsl(215, 16%, 70%)' },
                        grid: { color: 'rgba(255, 255, 255, 0.05)' },
                        ticks: { color: 'hsl(215, 12%, 48%)' },
                        min: 35,
                        max: 105
                    },
                    y: {
                        title: { display: true, text: 'Final Exam Score (/100)', color: 'hsl(215, 16%, 70%)' },
                        grid: { color: 'rgba(255, 255, 255, 0.05)' },
                        ticks: { color: 'hsl(215, 12%, 48%)' },
                        min: 0,
                        max: 105
                    }
                }
            }
        });
    } else {
        // Weekly Study Hours Trend (Line Chart showing mean)
        impactChartInstance = new Chart(ctx, {
            type: 'line',
            data: {
                datasets: [{
                    label: 'Average Final Grade',
                    data: chartDataCache.study_hours_impact,
                    backgroundColor: 'rgba(168, 85, 247, 0.2)',
                    borderColor: 'rgba(168, 85, 247, 1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.35,
                    pointBackgroundColor: 'rgba(0, 242, 254, 1)',
                    pointRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: {
                        type: 'linear',
                        title: { display: true, text: 'Study Hours Weekly (Hours)', color: 'hsl(215, 16%, 70%)' },
                        grid: { color: 'rgba(255, 255, 255, 0.05)' },
                        ticks: { color: 'hsl(215, 12%, 48%)' },
                        min: 0,
                        max: 30
                    },
                    y: {
                        title: { display: true, text: 'Average Final Score', color: 'hsl(215, 16%, 70%)' },
                        grid: { color: 'rgba(255, 255, 255, 0.05)' },
                        ticks: { color: 'hsl(215, 12%, 48%)' },
                        min: 10,
                        max: 105
                    }
                }
            }
        });
    }
}

function switchChart(type) {
    activeChartType = type;
    document.getElementById('btn-chart-scatter').classList.toggle('active', type === 'scatter');
    document.getElementById('btn-chart-line').classList.toggle('active', type === 'line');
    renderImpactChart();
}

// Setup live prediction slider bindings
function setupInputListeners() {
    const sliders = [
        { id: 'input-attendance', valId: 'val-attendance', suffix: '%' },
        { id: 'input-study-hours', valId: 'val-study-hours', suffix: ' hrs' },
        { id: 'input-midterm', valId: 'val-midterm', suffix: '' },
        { id: 'input-assignments', valId: 'val-assignments', suffix: '%' }
    ];
    
    sliders.forEach(slider => {
        const el = document.getElementById(slider.id);
        const valEl = document.getElementById(slider.valId);
        
        el.addEventListener('input', () => {
            valEl.innerText = el.value + slider.suffix;
            triggerPrediction();
        });
    });
    
    document.getElementById('input-sleep').addEventListener('input', triggerPrediction);
    document.getElementById('input-screen').addEventListener('input', triggerPrediction);
    
    // Initial call to trigger first prediction output
    triggerPrediction();
}

// Predict performance from sliders
let predictionTimeout = null;
function triggerPrediction() {
    // Debounce predictions to 100ms to avoid clogging backend requests while sliding rapidly
    clearTimeout(predictionTimeout);
    predictionTimeout = setTimeout(() => {
        const payload = {
            attendance_rate: parseFloat(document.getElementById('input-attendance').value),
            study_hours_weekly: parseFloat(document.getElementById('input-study-hours').value),
            sleep_hours_daily: parseFloat(document.getElementById('input-sleep').value),
            screen_time_daily: parseFloat(document.getElementById('input-screen').value),
            assignment_completion_rate: parseFloat(document.getElementById('input-assignments').value),
            midterm_score: parseFloat(document.getElementById('input-midterm').value)
        };
        
        fetch('/api/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
        .then(response => {
            if (!response.ok) throw new Error("Prediction failed");
            return response.json();
        })
        .then(data => {
            document.getElementById('predicted-score-display').innerText = data.predicted_final_score + '%';
            document.getElementById('pass-probability-display').innerText = data.pass_probability + '%';
            
            const riskEl = document.getElementById('risk-level-display');
            riskEl.innerText = data.risk_level + ' Risk';
            riskEl.className = 'meta-val risk-badge ' + data.risk_level.toLowerCase();
            
            // Set risk bar color/width (fill represents failure risk, i.e. 100 - pass_probability)
            const failProb = (100 - data.pass_probability);
            document.getElementById('risk-bar-fill').style.width = failProb + '%';
            
            let desc = '';
            if (data.risk_level === 'High') {
                desc = '⚠️ High risk of failure. Immediate academic monitoring and supplementary instruction required.';
            } else if (data.risk_level === 'Medium') {
                desc = '⚡ Moderate risk. Recommend check-in with academic advisor to boost study habits.';
            } else {
                desc = '✅ Good standing. Student is highly likely to pass the course.';
            }
            document.getElementById('risk-description-text').innerText = desc;
        })
        .catch(err => {
            console.error("Prediction API Error:", err);
            document.getElementById('predicted-score-display').innerText = "Err";
            document.getElementById('pass-probability-display').innerText = "Err";
            document.getElementById('risk-level-display').innerText = "Unavailable";
            document.getElementById('risk-level-display').className = 'meta-val risk-badge';
            document.getElementById('risk-bar-fill').style.width = '0%';
            document.getElementById('risk-description-text').innerText = "Please make sure models are trained by running the ML pipeline.";
        });
    }, 100);
}

// SQL Analytical Engine logic
function loadSqlQueryText() {
    const selected = document.getElementById('sql-query-select').value;
    document.getElementById('sql-query-code').innerText = sqlQueriesCode[selected];
}

function executeSqlQuery() {
    const selected = document.getElementById('sql-query-select').value;
    
    fetch('/api/run-sql', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query_type: selected })
    })
    .then(response => {
        if (!response.ok) throw new Error("SQL Execution error");
        return response.json();
    })
    .then(data => {
        const table = document.getElementById('sql-results-table');
        table.innerHTML = '';
        
        // Rows count
        document.getElementById('sql-rows-count').innerText = data.records.length + " Rows";
        
        // Add header
        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        data.columns.forEach(col => {
            const th = document.createElement('th');
            // Format column names for readability (replace underscore with space, capitalize)
            th.innerText = col.replace(/_/g, ' ').toUpperCase();
            headerRow.appendChild(th);
        });
        thead.appendChild(headerRow);
        table.appendChild(thead);
        
        // Add body
        const tbody = document.createElement('tbody');
        data.records.forEach(row => {
            const tr = document.createElement('tr');
            data.columns.forEach(col => {
                const td = document.createElement('td');
                td.innerText = row[col] !== null ? row[col] : 'NULL';
                tr.appendChild(td);
            });
            tbody.appendChild(tr);
        });
        table.appendChild(tbody);
    })
    .catch(err => {
        console.error("SQL Engine Error:", err);
        const table = document.getElementById('sql-results-table');
        table.innerHTML = `<thead><tr><th>Error</th></tr></thead><tbody><tr><td>Failed to fetch SQL results. Make sure SQL database is setup.</td></tr></tbody>`;
        document.getElementById('sql-rows-count').innerText = "0 Rows";
    });
}
