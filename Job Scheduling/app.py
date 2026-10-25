"""
Job Scheduling System - Flask Web Application
Provides interactive simulation, visualization, job management, and comparative analytics
for Greedy and Dynamic Programming job scheduling algorithms.
"""

import os
import sqlite3
import json
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = "chrono-sync-secret-key-phase3"
DB_PATH = os.path.join(os.path.dirname(__file__), "database.db")

# Resource Options
RESOURCE_TYPES = ["Employee", "Machine", "Computer", "Vehicle", "Other"]
RESOURCE_STATUSES = ["Available", "Busy", "Unavailable"]

# Color palette for job visualization
JOB_COLORS = [
    "#6366F1", "#38BDF8", "#10B981", "#F59E0B", "#EC4899",
    "#8B5CF6", "#06B6D4", "#14B8A6", "#F97316", "#A855F7",
    "#3B82F6", "#EF4444", "#84CC16", "#D946EF", "#0EA5E9"
]

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes tables and seeds initial sample dataset if empty."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Jobs Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            arrival_time INTEGER NOT NULL DEFAULT 0,
            burst_time INTEGER NOT NULL DEFAULT 1,
            priority INTEGER NOT NULL DEFAULT 1,
            deadline INTEGER NOT NULL DEFAULT 10,
            profit INTEGER NOT NULL DEFAULT 50,
            cpu_req INTEGER NOT NULL DEFAULT 1,
            mem_req INTEGER NOT NULL DEFAULT 2,
            color TEXT,
            status TEXT DEFAULT 'Ready',
            required_resource TEXT DEFAULT '',
            assigned_resource_id TEXT DEFAULT NULL,
            missed_reason TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Safely ensure required_resource, assigned_resource_id and missed_reason exist on jobs
    cursor.execute("PRAGMA table_info(jobs)")
    job_cols = [c[1] for c in cursor.fetchall()]
    if "required_resource" not in job_cols:
        cursor.execute("ALTER TABLE jobs ADD COLUMN required_resource TEXT DEFAULT ''")
    if "assigned_resource_id" not in job_cols:
        cursor.execute("ALTER TABLE jobs ADD COLUMN assigned_resource_id TEXT DEFAULT NULL")
    if "missed_reason" not in job_cols:
        cursor.execute("ALTER TABLE jobs ADD COLUMN missed_reason TEXT DEFAULT ''")

    # Phase 4 Schedules Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            job_name TEXT NOT NULL,
            processing_time REAL NOT NULL,
            deadline REAL NOT NULL,
            start_time REAL NOT NULL,
            end_time REAL NOT NULL,
            resource_id TEXT NOT NULL,
            resource_name TEXT NOT NULL,
            profit REAL NOT NULL,
            priority TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Scheduled',
            algorithm TEXT NOT NULL DEFAULT 'Greedy',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(job_id) REFERENCES jobs(id)
        )
    """)

    # Phase 3 Resources Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resource_id TEXT UNIQUE NOT NULL,
            resource_name TEXT NOT NULL,
            resource_type TEXT NOT NULL,
            available_hours REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'Available'
        )
    """)

    # Safely verify resources columns
    cursor.execute("PRAGMA table_info(resources)")
    res_cols = [c[1] for c in cursor.fetchall()]
    if "resource_id" not in res_cols:
        cursor.execute("ALTER TABLE resources ADD COLUMN resource_id TEXT UNIQUE NOT NULL DEFAULT ''")
    if "resource_name" not in res_cols:
        cursor.execute("ALTER TABLE resources ADD COLUMN resource_name TEXT NOT NULL DEFAULT ''")
    if "resource_type" not in res_cols:
        cursor.execute("ALTER TABLE resources ADD COLUMN resource_type TEXT NOT NULL DEFAULT 'Other'")
    if "available_hours" not in res_cols:
        cursor.execute("ALTER TABLE resources ADD COLUMN available_hours REAL NOT NULL DEFAULT 8.0")
    if "status" not in res_cols:
        cursor.execute("ALTER TABLE resources ADD COLUMN status TEXT NOT NULL DEFAULT 'Available'")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_resources (
            id INTEGER PRIMARY KEY,
            total_cpu_cores INTEGER DEFAULT 8,
            total_memory_gb INTEGER DEFAULT 32
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS execution_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            algorithm_name TEXT NOT NULL,
            algorithm_key TEXT NOT NULL,
            total_jobs INTEGER NOT NULL,
            makespan INTEGER NOT NULL,
            avg_waiting_time REAL NOT NULL,
            avg_turnaround_time REAL NOT NULL,
            total_profit INTEGER NOT NULL,
            cpu_utilization REAL NOT NULL,
            executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Phase 6 Benchmark Results Table (Requirement 9)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS benchmark_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dataset_size TEXT NOT NULL,
            num_jobs INTEGER NOT NULL,
            algorithm TEXT NOT NULL,
            execution_time REAL NOT NULL,
            min_execution_time REAL DEFAULT 0.0,
            max_execution_time REAL DEFAULT 0.0,
            jobs_scheduled INTEGER NOT NULL,
            jobs_missed INTEGER NOT NULL,
            total_profit REAL NOT NULL,
            processing_time REAL NOT NULL,
            resource_utilization REAL NOT NULL,
            deadline_success_rate REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Seed system resources if empty
    cursor.execute("SELECT COUNT(*) FROM system_resources")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO system_resources (id, total_cpu_cores, total_memory_gb) VALUES (1, 8, 32)")

    # Seed default sample jobs if table is empty
    cursor.execute("SELECT COUNT(*) FROM jobs")
    if cursor.fetchone()[0] == 0:
        seed_preset_jobs(cursor, "cloud_microservices")

    # Seed initial Phase 3 resources if empty
    cursor.execute("SELECT COUNT(*) FROM resources")
    if cursor.fetchone()[0] == 0:
        seed_default_resources(cursor)

    conn.commit()
    conn.close()


def seed_default_resources(cursor):
    """Seeds initial sample resources if resources table is empty."""
    default_resources = [
        ("R001", "Developer 1", "Employee", 8.0, "Available"),
        ("R002", "Machine 1", "Machine", 12.0, "Available"),
        ("R003", "Compute Node 1", "Computer", 16.0, "Available"),
        ("R004", "Delivery Van 1", "Vehicle", 6.0, "Busy"),
        ("R005", "Senior Architect", "Employee", 8.0, "Unavailable")
    ]
    for r in default_resources:
        cursor.execute("""
            INSERT INTO resources (resource_id, resource_name, resource_type, available_hours, status)
            VALUES (?, ?, ?, ?, ?)
        """, r)


def seed_preset_jobs(cursor, preset_name: str):
    """Inserts realistic presets."""
    presets = {
        "cloud_microservices": [
            ("Auth Service", 0, 3, 1, 5, 80, 2, 4, "#6366F1", "Employee"),
            ("Payment Gateway", 1, 4, 1, 7, 120, 4, 8, "#EC4899", "Computer"),
            ("Data Sync Worker", 2, 6, 3, 12, 60, 2, 4, "#38BDF8", "Machine"),
            ("Email Dispatcher", 3, 2, 4, 8, 40, 1, 2, "#10B981", "Employee"),
            ("Analytics Ingest", 4, 5, 2, 14, 90, 3, 6, "#F59E0B", "Computer"),
            ("Report Generator", 6, 3, 3, 15, 75, 2, 4, "#8B5CF6", "Machine")
        ],
        "realtime_dsp": [
            ("Audio Buffer Flush", 0, 2, 1, 3, 100, 2, 2, "#EF4444", "Computer"),
            ("FFT Spectrum Filter", 1, 3, 2, 5, 110, 4, 8, "#3B82F6", "Machine"),
            ("Echo Cancellation", 2, 2, 1, 6, 95, 2, 4, "#10B981", "Employee"),
            ("Spatial Encoder", 3, 4, 2, 9, 85, 4, 6, "#F59E0B", "Machine"),
            ("Stream Multiplexer", 5, 2, 3, 10, 70, 1, 2, "#8B5CF6", "Computer")
        ],
        "high_contention": [
            ("Task Alpha", 0, 5, 3, 8, 50, 2, 4, "#6366F1", "Employee"),
            ("Task Beta", 0, 2, 1, 4, 90, 1, 2, "#10B981", "Employee"),
            ("Task Gamma", 1, 1, 2, 3, 70, 1, 2, "#38BDF8", "Computer"),
            ("Task Delta", 2, 4, 4, 10, 40, 2, 4, "#F59E0B", "Machine"),
            ("Task Epsilon", 2, 3, 1, 7, 130, 2, 6, "#EC4899", "Vehicle"),
            ("Task Zeta", 3, 2, 2, 6, 80, 1, 2, "#8B5CF6", "Other")
        ],
        "profit_maximizer": [
            ("Enterprise Backup", 0, 6, 4, 8, 60, 2, 8, "#38BDF8", "Machine"),
            ("High-Frequency Arbitrage", 1, 2, 1, 3, 250, 4, 8, "#10B981", "Computer"),
            ("Core Ledger Commit", 2, 3, 1, 6, 200, 4, 12, "#6366F1", "Employee"),
            ("Security Vulnerability Scan", 3, 5, 3, 12, 110, 2, 4, "#F59E0B", "Employee"),
            ("Customer KYC Check", 4, 2, 2, 7, 140, 1, 4, "#EC4899", "Employee")
        ]
    }

    selected = presets.get(preset_name, presets["cloud_microservices"])
    for job in selected:
        req_res = job[9] if len(job) > 9 else ""
        cursor.execute("""
            INSERT INTO jobs (name, arrival_time, burst_time, priority, deadline, profit, cpu_req, mem_req, color, required_resource)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (job[0], job[1], job[2], job[3], job[4], job[5], job[6], job[7], job[8], req_res))


def get_all_jobs():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jobs ORDER BY arrival_time ASC, id ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


# ==========================================
# PHASE 7 JOB VALIDATION & DEMO DATA
# ==========================================

def validate_job_data(data: dict, editing_id: int = None):
    """
    Validates job input both client & server-side:
    - Name / Job ID: Required, Unique
    - Burst / Processing Time: Required, Integer > 0
    - Deadline: Required, Integer > 0, Must be >= burst_time
    - Profit: Required, Numeric >= 0
    - Priority: Integer >= 1
    - Arrival Time: Integer >= 0
    """
    errors = {}
    name = (data.get("name") or "").strip()
    burst_raw = str(data.get("burst_time") if data.get("burst_time") is not None else data.get("processing_time") or "").strip()
    deadline_raw = str(data.get("deadline") if data.get("deadline") is not None else "").strip()
    profit_raw = str(data.get("profit") if data.get("profit") is not None else "").strip()
    priority_raw = str(data.get("priority") if data.get("priority") is not None else "1").strip()
    arrival_raw = str(data.get("arrival_time") if data.get("arrival_time") is not None else "0").strip()

    # 1. Job Name / Identifier
    if not name:
        errors["name"] = "Job Name / Identifier is required."
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        if editing_id:
            cursor.execute("SELECT id FROM jobs WHERE name = ? AND id != ?", (name, editing_id))
        else:
            cursor.execute("SELECT id FROM jobs WHERE name = ?", (name,))
        if cursor.fetchone():
            errors["name"] = f"Job '{name}' already exists. Job ID/Name must be unique."
        conn.close()

    # 2. Burst Time (Processing Time)
    burst_time = 0
    if not burst_raw:
        errors["burst_time"] = "Processing time (burst time) is required."
    else:
        try:
            burst_time = int(burst_raw)
            if burst_time <= 0:
                errors["burst_time"] = "Processing time must be a positive integer greater than 0."
        except ValueError:
            errors["burst_time"] = "Processing time must be a valid integer."

    # 3. Deadline
    if not deadline_raw:
        errors["deadline"] = "Deadline is required."
    else:
        try:
            deadline = int(deadline_raw)
            if deadline <= 0:
                errors["deadline"] = "Deadline must be greater than 0."
            elif burst_time > 0 and deadline < burst_time:
                errors["deadline"] = "Deadline must be greater than or equal to processing time."
        except ValueError:
            errors["deadline"] = "Deadline must be a valid integer."

    # 4. Profit
    if not profit_raw and profit_raw != "0":
        errors["profit"] = "Profit is required."
    else:
        try:
            profit = float(profit_raw)
            if profit < 0:
                errors["profit"] = "Profit must be greater than or equal to 0."
        except ValueError:
            errors["profit"] = "Profit must be a valid number."

    # 5. Priority
    if priority_raw:
        try:
            prio = int(priority_raw)
            if prio < 1:
                errors["priority"] = "Priority must be at least 1 (1 = Highest)."
        except ValueError:
            errors["priority"] = "Priority must be a valid integer."

    # 6. Arrival Time
    if arrival_raw:
        try:
            arr = int(arrival_raw)
            if arr < 0:
                errors["arrival_time"] = "Arrival time cannot be negative."
        except ValueError:
            errors["arrival_time"] = "Arrival time must be a valid integer."

    return len(errors) == 0, errors


def load_official_demo_data(cursor, overwrite: bool = False):
    """
    Seeds official demonstration dataset containing at least 8 jobs (J001-J008)
    and at least 3 resources with realistic, diverse constraints.
    Safe and non-destructive unless overwrite=True.
    """
    if overwrite:
        cursor.execute("DELETE FROM schedules")
        cursor.execute("DELETE FROM jobs")
        cursor.execute("DELETE FROM resources")

    # 1. Seed Resources (At least 3 realistic types)
    demo_resources = [
        ("R001", "Developer Lead", "Employee", 8.0, "Available"),
        ("R002", "Production Database Server", "Machine", 12.0, "Available"),
        ("R003", "HPC Compute Cluster", "Computer", 16.0, "Available"),
        ("R004", "QA Automation Engineer", "Employee", 8.0, "Available")
    ]
    for r in demo_resources:
        cursor.execute("""
            INSERT OR IGNORE INTO resources (resource_id, resource_name, resource_type, available_hours, status)
            VALUES (?, ?, ?, ?, ?)
        """, r)

    # 2. Seed Jobs (At least 8 jobs with varying burst, deadline, profit, priority, and required resource)
    demo_jobs = [
        ("J001 Website Development", 0, 3, 2, 6, 90, 2, 4, "#6366F1", "Employee"),
        ("J002 Database Backup", 0, 2, 1, 4, 80, 4, 8, "#38BDF8", "Machine"),
        ("J003 Software Testing", 1, 4, 3, 9, 120, 2, 4, "#10B981", "Employee"),
        ("J004 Documentation", 1, 2, 4, 5, 40, 1, 2, "#F59E0B", "Employee"),
        ("J005 Server Maintenance", 2, 3, 1, 7, 110, 4, 8, "#EC4899", "Machine"),
        ("J006 API Development", 2, 5, 2, 11, 150, 2, 6, "#8B5CF6", "Employee"),
        ("J007 UI Design", 3, 3, 3, 7, 85, 2, 4, "#06B6D4", "Employee"),
        ("J008 Data Processing", 3, 4, 2, 10, 130, 4, 8, "#14B8A6", "Computer")
    ]
    for j in demo_jobs:
        cursor.execute("""
            INSERT INTO jobs (name, arrival_time, burst_time, priority, deadline, profit, cpu_req, mem_req, color, required_resource, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending')
        """, j)


# ==========================================
# PHASE 3 RESOURCE HELPERS & VALIDATION
# ==========================================

def validate_resource_data(data: dict, editing_id: int = None):
    """
    Validates resource input:
    - Resource ID: Required, Unique
    - Resource Name: Required, Minimum 2 chars
    - Resource Type: Required, in RESOURCE_TYPES
    - Available Hours: Required, positive number > 0, max 24
    - Status: Required, in RESOURCE_STATUSES
    """
    errors = {}
    resource_id = (data.get("resource_id") or "").strip()
    resource_name = (data.get("resource_name") or "").strip()
    resource_type = (data.get("resource_type") or "").strip()
    available_hours_raw = str(data.get("available_hours") or "").strip()
    status = (data.get("status") or "").strip()

    # 1. Resource ID
    if not resource_id:
        errors["resource_id"] = "Resource ID is required."
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        if editing_id:
            cursor.execute("SELECT id FROM resources WHERE resource_id = ? AND id != ?", (resource_id, editing_id))
        else:
            cursor.execute("SELECT id FROM resources WHERE resource_id = ?", (resource_id,))
        if cursor.fetchone():
            errors["resource_id"] = f"Resource ID '{resource_id}' already exists. Must be unique."
        conn.close()

    # 2. Resource Name
    if not resource_name:
        errors["resource_name"] = "Resource Name is required."
    elif len(resource_name) < 2:
        errors["resource_name"] = "Resource Name must be at least 2 characters."

    # 3. Resource Type
    if not resource_type:
        errors["resource_type"] = "Resource Type is required."
    elif resource_type not in RESOURCE_TYPES:
        errors["resource_type"] = f"Invalid Resource Type. Allowed: {', '.join(RESOURCE_TYPES)}."

    # 4. Available Hours
    if not available_hours_raw:
        errors["available_hours"] = "Available Hours is required."
    else:
        try:
            val = float(available_hours_raw)
            if val <= 0:
                errors["available_hours"] = "Available Hours must be a positive number greater than 0."
            elif val > 24.0:
                errors["available_hours"] = "Available Hours cannot exceed 24 hours."
        except ValueError:
            errors["available_hours"] = "Available Hours must be a valid numeric value."

    # 5. Status
    if not status:
        errors["status"] = "Status is required."
    elif status not in RESOURCE_STATUSES:
        errors["status"] = f"Invalid Status. Allowed: {', '.join(RESOURCE_STATUSES)}."

    return len(errors) == 0, errors


def calculate_resource_utilization():
    """
    Calculates:
    - Total Resource Hours
    - Used Resource Hours (from assigned/scheduled jobs; 0 if none)
    - Available Resource Hours
    - Resource Utilization Percentage: (Used Resource Hours / Total Resource Hours) * 100
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT SUM(available_hours) FROM resources")
    total_val = cursor.fetchone()[0]
    total_hours = round(float(total_val), 2) if total_val is not None else 0.0

    # Query for assigned scheduled jobs
    cursor.execute("""
        SELECT SUM(burst_time) FROM jobs
        WHERE assigned_resource_id IS NOT NULL 
          AND status IN ('Scheduled', 'Running', 'Assigned')
    """)
    used_val = cursor.fetchone()[0]
    used_hours = round(float(used_val), 2) if used_val is not None else 0.0

    conn.close()

    available_hours = round(max(0.0, total_hours - used_hours), 2)
    if total_hours > 0:
        utilization_pct = round((used_hours / total_hours) * 100.0, 2)
    else:
        utilization_pct = 0.0

    return {
        "total_hours": total_hours,
        "used_hours": used_hours,
        "available_hours": available_hours,
        "utilization_percentage": utilization_pct
    }


def find_available_resources(query_str: str = None):
    """
    Finds available resources matching resource_type OR resource_name OR resource_id.
    Prepares validation for future DAA algorithm allocation.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    if query_str:
        pattern = f"%{query_str}%"
        cursor.execute("""
            SELECT * FROM resources
            WHERE status = 'Available'
              AND (resource_type LIKE ? OR resource_name LIKE ? OR resource_id LIKE ?)
            ORDER BY id ASC
        """, (pattern, pattern, pattern))
    else:
        cursor.execute("SELECT * FROM resources WHERE status = 'Available' ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def resource_exists(identifier: str) -> bool:
    """Checks if a resource exists by resource_id or primary key id."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM resources WHERE resource_id = ? OR id = ?", (identifier, identifier))
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0


def is_resource_associated_with_jobs(resource_id: str, resource_name: str = "") -> bool:
    """
    Checks if a resource is currently associated with scheduled/assigned jobs
    or active schedule allocations. Enforces delete protection.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM jobs
        WHERE assigned_resource_id = ? 
           OR required_resource = ? 
           OR (required_resource = ? AND required_resource != '')
    """, (resource_id, resource_id, resource_name))
    job_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM schedules
        WHERE resource_id = ? OR resource_name = ?
    """, (resource_id, resource_name))
    sched_count = cursor.fetchone()[0]

    conn.close()
    return (job_count + sched_count) > 0


def get_jobs_for_resource(resource_id: str, resource_name: str = ""):
    """Returns all jobs associated with a given resource."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM jobs
        WHERE assigned_resource_id = ? 
           OR required_resource = ? 
           OR (required_resource = ? AND required_resource != '')
        ORDER BY arrival_time ASC, id ASC
    """, (resource_id, resource_id, resource_name))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ==========================================
# PAGE ROUTES
# ==========================================

@app.route("/")
def index():
    """Dashboard homepage with real database resource counts & scheduling metrics."""
    jobs = get_all_jobs()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM execution_history ORDER BY id DESC LIMIT 5")
    recent_history = [dict(r) for r in cursor.fetchall()]
    cursor.execute("SELECT * FROM system_resources WHERE id = 1")
    resources_sys = dict(cursor.fetchone() or {"total_cpu_cores": 8, "total_memory_gb": 32})

    # Real database resource counts
    cursor.execute("SELECT COUNT(*) FROM resources")
    total_resources = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM resources WHERE status = 'Available'")
    available_resources = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM resources WHERE status = 'Busy'")
    busy_resources = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM resources WHERE status = 'Unavailable'")
    unavailable_resources = cursor.fetchone()[0]

    # Phase 4 Real Scheduling Statistics (Section 18)
    cursor.execute("SELECT COUNT(*) FROM jobs")
    total_jobs_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE status IN ('Pending', 'Ready')")
    pending_jobs_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE status = 'Scheduled'")
    scheduled_jobs_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE status = 'Missed'")
    missed_jobs_count = cursor.fetchone()[0]
    cursor.execute("SELECT SUM(profit) FROM schedules")
    total_profit_val = cursor.fetchone()[0]
    total_scheduled_profit = float(total_profit_val) if total_profit_val is not None else 0.0

    from algorithms.scheduler import get_current_schedule_service
    sched_telemetry = get_current_schedule_service(conn)
    resource_utilization_pct = sched_telemetry["metrics"]["resource_utilization"]

    # Phase 6: Latest Algorithm Comparison integration (Requirement 23)
    cursor.execute("""
        SELECT * FROM benchmark_results 
        ORDER BY id DESC LIMIT 4
    """)
    latest_bench_rows = [dict(r) for r in cursor.fetchall()]
    latest_comparison = None
    if latest_bench_rows:
        g_run = next((r for r in latest_bench_rows if r["algorithm"] == "Greedy"), None)
        dp_run = next((r for r in latest_bench_rows if r["algorithm"] == "Dynamic Programming"), None)
        latest_comparison = {
            "dataset_size": latest_bench_rows[0]["dataset_size"].capitalize(),
            "num_jobs": latest_bench_rows[0]["num_jobs"],
            "greedy_time": g_run["execution_time"] if g_run else None,
            "dp_time": dp_run["execution_time"] if dp_run else None,
            "compared_at": latest_bench_rows[0]["created_at"]
        }

    conn.close()

    total_burst = sum(j["burst_time"] for j in jobs)
    total_potential_profit = sum(j["profit"] for j in jobs)
    utilization = calculate_resource_utilization()

    return render_template(
        "index.html",
        jobs=jobs,
        job_count=len(jobs),
        total_burst=total_burst,
        total_profit=total_potential_profit,
        recent_history=recent_history,
        resources=resources_sys,
        total_resources=total_resources,
        available_resources=available_resources,
        busy_resources=busy_resources,
        unavailable_resources=unavailable_resources,
        total_jobs_count=total_jobs_count,
        pending_jobs_count=pending_jobs_count,
        scheduled_jobs_count=scheduled_jobs_count,
        missed_jobs_count=missed_jobs_count,
        total_scheduled_profit=total_scheduled_profit,
        resource_utilization_pct=resource_utilization_pct,
        utilization=utilization,
        latest_comparison=latest_comparison
    )


@app.route("/jobs")
def jobs_view():
    """
    Phase 7 Job Management interface.
    Supports Search, Status Filtering, Priority Filtering, and telemetry counts.
    """
    search_query = request.args.get("search", "").strip()
    status_filter = request.args.get("status", "All").strip()
    priority_filter = request.args.get("priority", "All").strip()

    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM jobs WHERE 1=1"
    params = []

    if search_query:
        pattern = f"%{search_query}%"
        query += " AND (name LIKE ? OR id LIKE ? OR required_resource LIKE ?)"
        params.extend([pattern, pattern, pattern])

    if status_filter and status_filter != "All":
        if status_filter == "Pending":
            query += " AND status IN ('Pending', 'Ready')"
        else:
            query += " AND status = ?"
            params.append(status_filter)

    if priority_filter and priority_filter != "All":
        try:
            p_val = int(priority_filter)
            query += " AND priority = ?"
            params.append(p_val)
        except ValueError:
            pass

    query += " ORDER BY arrival_time ASC, id ASC"
    cursor.execute(query, params)
    jobs = [dict(r) for r in cursor.fetchall()]

    # Real counts for badge metrics
    cursor.execute("SELECT COUNT(*) FROM jobs")
    total_jobs_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE status IN ('Pending', 'Ready')")
    pending_jobs_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE status = 'Scheduled'")
    scheduled_jobs_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE status = 'Missed'")
    missed_jobs_count = cursor.fetchone()[0]

    cursor.execute("SELECT DISTINCT resource_type FROM resources WHERE status = 'Available'")
    available_types = [r[0] for r in cursor.fetchall()]

    conn.close()

    return render_template(
        "jobs.html",
        jobs=jobs,
        search_query=search_query,
        status_filter=status_filter,
        priority_filter=priority_filter,
        total_jobs_count=total_jobs_count,
        pending_jobs_count=pending_jobs_count,
        scheduled_jobs_count=scheduled_jobs_count,
        missed_jobs_count=missed_jobs_count,
        available_types=available_types
    )


@app.route("/schedule")
def schedule_view():
    """
    Phase 4 & Phase 5: Job Schedule interface.
    Displays current schedule, summary cards, and controls to execute
    either Greedy Algorithm or Dynamic Programming.
    """
    conn = get_db_connection()
    from algorithms.scheduler import get_current_schedule_service
    from algorithms.dynamic_programming import dynamic_programming_job_scheduling
    sched_data = get_current_schedule_service(conn)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jobs ORDER BY arrival_time ASC, id ASC")
    all_jobs = [dict(r) for r in cursor.fetchall()]
    cursor.execute("SELECT * FROM resources WHERE status = 'Available' ORDER BY id ASC")
    avail_resources = [dict(r) for r in cursor.fetchall()]
    
    # Check latest execution from history
    cursor.execute("SELECT * FROM execution_history ORDER BY id DESC LIMIT 1")
    latest_hist = cursor.fetchone()
    conn.close()

    latest_hist_dict = dict(latest_hist) if latest_hist else None
    algorithm_used = sched_data.get("algorithm_used") or "Greedy"
    exec_time = 0.00042
    capacity_t = 0
    if latest_hist_dict:
        try:
            exec_time = float(latest_hist_dict.get("avg_waiting_time", 0.00042))
            capacity_t = int(latest_hist_dict.get("avg_turnaround_time", 0))
        except (KeyError, ValueError, TypeError):
            exec_time = 0.00042
        alg_name = str(latest_hist_dict.get("algorithm_name") or "")
        if "Dynamic Programming" in alg_name:
            algorithm_used = "Dynamic Programming"
        elif "Greedy" in alg_name:
            algorithm_used = "Greedy"

    # If schedules currently exist in the database, prioritize their actual algorithm tag
    if sched_data.get("schedules"):
        algorithm_used = sched_data.get("algorithm_used") or algorithm_used

    # DP grid visualization calculation if DP is active
    dp_grid = {"is_visualizable": False, "message": "Run Dynamic Programming to view the DP Table."}
    if algorithm_used == "Dynamic Programming":
        eval_jobs = [dict(j, status="Pending") for j in all_jobs if j.get("status") in ["Pending", "Scheduled", "Missed"]]
        dp_calc = dynamic_programming_job_scheduling(eval_jobs, avail_resources)
        dp_grid = dp_calc.get("dp_grid", {})
        if not capacity_t:
            capacity_t = dp_calc.get("scheduling_capacity", 0)

    return render_template(
        "schedule.html",
        schedules=sched_data["schedules"],
        missed_jobs=sched_data["missed_jobs"],
        metrics=sched_data["metrics"],
        jobs=all_jobs,
        resources=avail_resources,
        latest_run=latest_hist_dict,
        execution_time=exec_time,
        algorithm_used=algorithm_used,
        dp_grid=dp_grid,
        capacity_t=capacity_t
    )


@app.route("/schedule/greedy", methods=["POST"])
def schedule_greedy():
    """
    Phase 4: Executes Greedy Job Scheduling Algorithm.
    Saves results into schedules table and updates job statuses.
    """
    conn = get_db_connection()
    from algorithms.scheduler import run_greedy_scheduler_service
    res = run_greedy_scheduler_service(conn)
    conn.close()

    if res.get("success"):
        flash(res["message"], "success")
    else:
        flash(res.get("message", "Could not complete scheduling."), "warning")

    if request.headers.get("Accept") == "application/json" or request.is_json:
        return jsonify(res)

    return redirect(url_for("schedule_results"))


@app.route("/schedule/greedy/results")
def schedule_results():
    """
    Phase 4: Displays latest Greedy scheduling results.
    """
    conn = get_db_connection()
    from algorithms.scheduler import get_current_schedule_service
    sched_data = get_current_schedule_service(conn)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jobs ORDER BY arrival_time ASC, id ASC")
    all_jobs = [dict(r) for r in cursor.fetchall()]
    cursor.execute("SELECT * FROM resources WHERE status = 'Available' ORDER BY id ASC")
    avail_resources = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT * FROM execution_history WHERE algorithm_key = 'greedy_daa' ORDER BY id DESC LIMIT 1")
    latest_hist = cursor.fetchone()
    conn.close()

    exec_time = 0.00042
    if latest_hist:
        try:
            exec_time = float(latest_hist["avg_waiting_time"])
        except (KeyError, ValueError, TypeError):
            exec_time = 0.00042

    return render_template(
        "schedule.html",
        schedules=sched_data["schedules"],
        missed_jobs=sched_data["missed_jobs"],
        metrics=sched_data["metrics"],
        jobs=all_jobs,
        resources=avail_resources,
        latest_run=dict(latest_hist) if latest_hist else None,
        execution_time=exec_time,
        algorithm_used="Greedy",
        dp_grid={"is_visualizable": False, "message": "Run Dynamic Programming to view the DP Table."},
        capacity_t=0
    )


# ==============================================================================
# PHASE 5: DYNAMIC PROGRAMMING FLASK ROUTES
# ==============================================================================

@app.route("/schedule/dynamic-programming", methods=["POST"])
def schedule_dynamic_programming():
    """
    Phase 5: Executes Dynamic Programming Job Scheduling Algorithm.
    Saves selected jobs into schedules table, updates job statuses to Scheduled/Missed,
    and logs performance metrics into execution_history.
    """
    conn = get_db_connection()
    from algorithms.scheduler import run_dp_scheduler_service
    res = run_dp_scheduler_service(conn)
    conn.close()

    if res.get("success"):
        flash(res["message"], "success")
    else:
        flash(res.get("message", "Could not complete Dynamic Programming scheduling."), "warning")

    if request.headers.get("Accept") == "application/json" or request.is_json:
        return jsonify(res)

    return redirect(url_for("schedule_dp_results"))


@app.route("/schedule/dynamic-programming/results")
def schedule_dp_results():
    """
    Phase 5: Displays latest Dynamic Programming scheduling results,
    summary cards, metrics, and expandable DP table visualization.
    """
    conn = get_db_connection()
    from algorithms.scheduler import get_current_schedule_service
    from algorithms.dynamic_programming import dynamic_programming_job_scheduling
    sched_data = get_current_schedule_service(conn)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jobs ORDER BY arrival_time ASC, id ASC")
    all_jobs = [dict(r) for r in cursor.fetchall()]
    cursor.execute("SELECT * FROM resources WHERE status = 'Available' ORDER BY id ASC")
    avail_resources = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT * FROM execution_history WHERE algorithm_key = 'dp_daa' ORDER BY id DESC LIMIT 1")
    latest_hist = cursor.fetchone()
    conn.close()

    exec_time = 0.00042
    capacity_t = 0
    if latest_hist:
        try:
            exec_time = float(latest_hist["avg_waiting_time"])
            capacity_t = int(latest_hist["avg_turnaround_time"])
        except (KeyError, ValueError, TypeError):
            exec_time = 0.00042

    # Reconstruct the exact DP table data for visualization using candidate jobs
    eval_jobs = [dict(j, status="Pending") for j in all_jobs if j.get("status") in ["Pending", "Scheduled", "Missed"]]
    dp_calc = dynamic_programming_job_scheduling(eval_jobs, avail_resources)
    dp_grid = dp_calc.get("dp_grid", {})
    if not capacity_t:
        capacity_t = dp_calc.get("scheduling_capacity", 0)

    return render_template(
        "schedule.html",
        schedules=sched_data["schedules"],
        missed_jobs=sched_data["missed_jobs"],
        metrics=sched_data["metrics"],
        jobs=all_jobs,
        resources=avail_resources,
        latest_run=dict(latest_hist) if latest_hist else None,
        execution_time=exec_time,
        algorithm_used="Dynamic Programming",
        dp_grid=dp_grid,
        capacity_t=capacity_t
    )


@app.route("/schedule/reset", methods=["POST"])
def schedule_reset():
    """
    Phase 4: Resets generated schedule.
    Restores jobs to 'Pending' and removes schedule records.
    """
    conn = get_db_connection()
    from algorithms.scheduler import reset_schedule_service
    res = reset_schedule_service(conn)
    conn.close()

    flash(res["message"], "success")

    if request.headers.get("Accept") == "application/json" or request.is_json:
        return jsonify(res)

    return redirect(url_for("schedule_view"))


# ==============================================================================
# PHASE 6: ALGORITHM COMPARISON & BENCHMARKING ROUTES
# ==============================================================================

@app.route("/comparison")
def comparison_view():
    """
    Phase 6: Algorithm Comparison and Performance Analysis interface.
    Compares Greedy Algorithm vs Dynamic Programming using identical datasets.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM benchmark_results 
        ORDER BY id DESC LIMIT 20
    """)
    history = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return render_template("comparison.html", history=history)


@app.route("/comparison/run", methods=["POST"])
def comparison_run():
    """
    Phase 6: Backend API for executing empirical benchmark comparisons.
    Receives dataset_size, custom_count, and repeat_runs.
    Evaluates Greedy and Dynamic Programming on identical inputs.
    Persists results in benchmark_results table and returns JSON response.
    """
    try:
        data = request.get_json(silent=True) or request.form.to_dict() or {}
        dataset_size = str(data.get("dataset_size", "small")).strip().lower()
        custom_count = data.get("custom_count")
        
        try:
            repeat_runs = int(data.get("repeat_runs", 5))
        except (ValueError, TypeError):
            repeat_runs = 5

        conn = get_db_connection()
        from algorithms.benchmark import run_benchmark_comparison
        result = run_benchmark_comparison(
            dataset_size=dataset_size,
            custom_count=custom_count,
            repeat_runs=repeat_runs,
            conn=conn
        )
        conn.close()

        if not result.get("success"):
            return jsonify(result), 400

        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": f"An error occurred during benchmark execution: {str(e)}"}), 500


@app.route("/api/benchmark/trend", methods=["GET"])
def api_benchmark_trend():
    """Phase 6: Returns multi-size scalability curve (10, 50, 100, 500) for execution time chart."""
    try:
        from algorithms.benchmark import get_multi_size_benchmark_trend
        trend_data = get_multi_size_benchmark_trend(repeat_runs=3)
        return jsonify({"success": True, "trend": trend_data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/resources")
def resources_view():
    """
    Phase 3 Resource Management interface.
    Supports combined Search and Filter with parameterized queries.
    """
    search_query = request.args.get("search", "").strip()
    status_filter = request.args.get("status", "All").strip()
    type_filter = request.args.get("type", "All").strip()

    conn = get_db_connection()
    cursor = conn.cursor()

    # Parameterized dynamic query
    query = "SELECT * FROM resources WHERE 1=1"
    params = []

    if search_query:
        pattern = f"%{search_query}%"
        query += " AND (resource_id LIKE ? OR resource_name LIKE ? OR resource_type LIKE ?)"
        params.extend([pattern, pattern, pattern])

    if status_filter and status_filter != "All":
        query += " AND status = ?"
        params.append(status_filter)

    if type_filter and type_filter != "All":
        query += " AND resource_type = ?"
        params.append(type_filter)

    query += " ORDER BY id ASC"
    cursor.execute(query, params)
    resources = [dict(r) for r in cursor.fetchall()]

    # Real counts
    cursor.execute("SELECT COUNT(*) FROM resources")
    total_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM resources WHERE status = 'Available'")
    available_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM resources WHERE status = 'Busy'")
    busy_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM resources WHERE status = 'Unavailable'")
    unavailable_count = cursor.fetchone()[0]

    conn.close()

    utilization = calculate_resource_utilization()

    return render_template(
        "resources.html",
        resources=resources,
        search_query=search_query,
        status_filter=status_filter,
        type_filter=type_filter,
        resource_types=RESOURCE_TYPES,
        resource_statuses=RESOURCE_STATUSES,
        total_count=total_count,
        available_count=available_count,
        busy_count=busy_count,
        unavailable_count=unavailable_count,
        utilization=utilization
    )


@app.route("/resources/add", methods=["GET", "POST"])
def resource_add():
    """Add Resource view & submission with server-side validation."""
    if request.method == "POST":
        data = {
            "resource_id": request.form.get("resource_id", "").strip(),
            "resource_name": request.form.get("resource_name", "").strip(),
            "resource_type": request.form.get("resource_type", "").strip(),
            "available_hours": request.form.get("available_hours", "").strip(),
            "status": request.form.get("status", "").strip()
        }
        is_valid, errors = validate_resource_data(data)
        if not is_valid:
            return render_template(
                "resource_form.html",
                mode="add",
                resource=data,
                errors=errors,
                resource_types=RESOURCE_TYPES,
                resource_statuses=RESOURCE_STATUSES
            ), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO resources (resource_id, resource_name, resource_type, available_hours, status)
            VALUES (?, ?, ?, ?, ?)
        """, (
            data["resource_id"],
            data["resource_name"],
            data["resource_type"],
            float(data["available_hours"]),
            data["status"]
        ))
        conn.commit()
        conn.close()
        flash(f"Resource '{data['resource_id']} - {data['resource_name']}' created successfully!", "success")
        return redirect(url_for("resources_view"))

    return render_template(
        "resource_form.html",
        mode="add",
        resource={"status": "Available", "available_hours": 8.0, "resource_type": "Employee"},
        errors={},
        resource_types=RESOURCE_TYPES,
        resource_statuses=RESOURCE_STATUSES
    )


@app.route("/resources/edit/<int:id>", methods=["GET", "POST"])
def resource_edit(id: int):
    """Edit Resource view & submission with server-side validation."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM resources WHERE id = ?", (id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        flash("Resource not found.", "error")
        return redirect(url_for("resources_view")), 404

    existing = dict(row)

    if request.method == "POST":
        data = {
            "resource_id": request.form.get("resource_id", "").strip(),
            "resource_name": request.form.get("resource_name", "").strip(),
            "resource_type": request.form.get("resource_type", "").strip(),
            "available_hours": request.form.get("available_hours", "").strip(),
            "status": request.form.get("status", "").strip()
        }
        is_valid, errors = validate_resource_data(data, editing_id=id)
        if not is_valid:
            data["id"] = id
            return render_template(
                "resource_form.html",
                mode="edit",
                resource=data,
                errors=errors,
                resource_types=RESOURCE_TYPES,
                resource_statuses=RESOURCE_STATUSES
            ), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE resources
            SET resource_id = ?, resource_name = ?, resource_type = ?, available_hours = ?, status = ?
            WHERE id = ?
        """, (
            data["resource_id"],
            data["resource_name"],
            data["resource_type"],
            float(data["available_hours"]),
            data["status"],
            id
        ))
        conn.commit()
        conn.close()
        flash(f"Resource '{data['resource_id']}' updated successfully!", "success")
        return redirect(url_for("resources_view"))

    return render_template(
        "resource_form.html",
        mode="edit",
        resource=existing,
        errors={},
        resource_types=RESOURCE_TYPES,
        resource_statuses=RESOURCE_STATUSES
    )


@app.route("/resources/delete/<int:id>", methods=["POST"])
def resource_delete(id: int):
    """
    Deletes a resource after enforcing delete protection.
    If associated with a scheduled job, refuses deletion with warning.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM resources WHERE id = ?", (id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        flash("Resource not found.", "error")
        return redirect(url_for("resources_view")), 404

    res = dict(row)

    # Check delete protection
    if is_resource_associated_with_jobs(res["resource_id"], res["resource_name"]):
        conn.close()
        flash("This resource is currently associated with scheduled jobs and cannot be deleted.", "warning")
        return redirect(url_for("resources_view"))

    cursor.execute("DELETE FROM resources WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash(f"Resource '{res['resource_id']} - {res['resource_name']}' deleted successfully.", "success")
    return redirect(url_for("resources_view"))


@app.route("/resources/view/<int:id>")
def resource_view(id: int):
    """View Resource details and currently assigned jobs."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM resources WHERE id = ?", (id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        flash("Resource not found.", "error")
        return redirect(url_for("resources_view")), 404

    res = dict(row)
    assigned_jobs = get_jobs_for_resource(res["resource_id"], res["resource_name"])

    return render_template(
        "resource_view.html",
        resource=res,
        assigned_jobs=assigned_jobs
    )



# ==========================================
# REST API ENDPOINTS
# ==========================================

@app.route("/api/jobs", methods=["GET", "POST"])
def api_jobs():
    if request.method == "GET":
        return jsonify({"success": True, "jobs": get_all_jobs()})
    
    # POST - Create new job with server-side validation
    data = request.json or request.form.to_dict() or {}
    is_valid, errors = validate_job_data(data)
    if not is_valid:
        first_err = next(iter(errors.values()))
        return jsonify({"success": False, "error": first_err, "errors": errors}), 400

    name = data.get("name", "").strip()
    arrival_time = int(data.get("arrival_time", 0))
    burst_time = int(data.get("burst_time") or data.get("processing_time") or 1)
    priority = int(data.get("priority", 1))
    deadline = int(data.get("deadline", arrival_time + burst_time))
    profit = float(data.get("profit", 50))
    cpu_req = max(1, int(data.get("cpu_req", 1)))
    mem_req = max(1, int(data.get("mem_req", 2)))
    req_res = data.get("required_resource", "").strip()
    
    color_index = len(get_all_jobs()) % len(JOB_COLORS)
    color = data.get("color") or JOB_COLORS[color_index]

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO jobs (name, arrival_time, burst_time, priority, deadline, profit, cpu_req, mem_req, color, required_resource, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending')
    """, (name, arrival_time, burst_time, priority, deadline, profit, cpu_req, mem_req, color, req_res))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()

    return jsonify({"success": True, "message": "Job created successfully", "job_id": new_id})


@app.route("/api/jobs/<int:job_id>", methods=["GET", "PUT", "DELETE"])
def api_job_detail(job_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return jsonify({"success": False, "error": f"Job #{job_id} not found."}), 404

    if request.method == "GET":
        job = dict(row)
        conn.close()
        return jsonify({"success": True, "job": job})

    if request.method == "DELETE":
        # Check active schedule protection
        cursor.execute("SELECT COUNT(*) FROM schedules WHERE job_id = ?", (job_id,))
        if cursor.fetchone()[0] > 0:
            conn.close()
            return jsonify({
                "success": False, 
                "error": "This job is currently scheduled. Please reset the schedule before deleting."
            }), 400

        cursor.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": f"Job #{job_id} deleted."})

    # PUT - update with server-side validation
    data = request.json or request.form.to_dict() or {}
    is_valid, errors = validate_job_data(data, editing_id=job_id)
    if not is_valid:
        conn.close()
        first_err = next(iter(errors.values()))
        return jsonify({"success": False, "error": first_err, "errors": errors}), 400

    name = data.get("name", "").strip()
    arrival_time = int(data.get("arrival_time", 0))
    burst_time = int(data.get("burst_time") or data.get("processing_time") or 1)
    priority = int(data.get("priority", 1))
    deadline = int(data.get("deadline", 10))
    profit = float(data.get("profit", 50))
    cpu_req = max(1, int(data.get("cpu_req", 1)))
    mem_req = max(1, int(data.get("mem_req", 2)))
    color = data.get("color", row["color"] or "#6366F1")
    req_res = data.get("required_resource", row["required_resource"] or "").strip()

    cursor.execute("""
        UPDATE jobs
        SET name = ?, arrival_time = ?, burst_time = ?, priority = ?, deadline = ?,
            profit = ?, cpu_req = ?, mem_req = ?, color = ?, required_resource = ?
        WHERE id = ?
    """, (name, arrival_time, burst_time, priority, deadline, profit, cpu_req, mem_req, color, req_res, job_id))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": f"Job #{job_id} updated."})


@app.route("/demo/load", methods=["POST"])
def demo_load():
    """
    Phase 7: Seeds the official demonstration dataset containing at least
    8 realistic jobs (J001-J008) and 4 resources across varying constraints.
    """
    data = request.get_json(silent=True) or request.form.to_dict() or {}
    overwrite = True if str(data.get("overwrite", "true")).lower() in ["true", "1", "yes"] else False
    
    conn = get_db_connection()
    cursor = conn.cursor()
    load_official_demo_data(cursor, overwrite=overwrite)
    conn.commit()
    conn.close()

    flash("Official DAA demonstration dataset loaded successfully (8 jobs, 4 resources).", "success")
    if request.headers.get("Accept") == "application/json" or request.is_json:
        return jsonify({"success": True, "message": "Demo data loaded successfully."})

    return redirect(url_for("jobs_view"))


@app.route("/about")
def about_view():
    """
    Phase 7: DAA Project Presentation and Theoretical Architecture page.
    Includes Problem Statement, Objectives, Greedy vs DP algorithms,
    Resource Allocation, Complexity Analysis, Benchmarking, and Tech Stack.
    """
    return render_template("about.html")


@app.errorhandler(404)
def page_not_found(e):
    """Clean 404 error handler with friendly user interface."""
    if request.path.startswith("/api/"):
        return jsonify({"success": False, "error": "The requested endpoint does not exist."}), 404
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_server_error(e):
    """Clean 500 error handler that protects system internals."""
    if request.path.startswith("/api/"):
        return jsonify({"success": False, "error": "An internal server error occurred."}), 500
    return render_template("500.html"), 500


@app.route("/api/jobs/reset", methods=["POST"])
def api_jobs_reset():
    """Resets jobs table to a specific preset or clears it."""
    data = request.json or {}
    preset = data.get("preset", "cloud_microservices")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM jobs")
    if preset != "empty":
        seed_preset_jobs(cursor, preset)
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": f"Jobs reset with preset: {preset}", "jobs": get_all_jobs()})


@app.route("/api/schedule/run", methods=["POST"])
def api_schedule_run():
    """Executes a single algorithm and returns full timeline and metrics."""
    from algorithms.scheduler import JobScheduler
    data = request.json or {}
    algo_key = data.get("algorithm", "fcfs")
    capacity = data.get("capacity")
    if capacity is not None:
        try:
            capacity = int(capacity)
        except ValueError:
            capacity = None

    jobs = get_all_jobs()
    result = JobScheduler.run_algorithm(algo_key, jobs, capacity=capacity)

    # Log to history
    if result["timeline"]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO execution_history (
                algorithm_name, algorithm_key, total_jobs, makespan,
                avg_waiting_time, avg_turnaround_time, total_profit, cpu_utilization
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            result["algorithm_name"],
            algo_key,
            result["metrics"]["total_jobs"],
            result["metrics"]["makespan"],
            result["metrics"]["avg_waiting_time"],
            result["metrics"]["avg_turnaround_time"],
            result["metrics"]["total_profit"],
            result["metrics"]["cpu_utilization"]
        ))
        conn.commit()
        conn.close()

    return jsonify({"success": True, "result": result})


@app.route("/api/schedule/compare", methods=["POST"])
def api_schedule_compare():
    """Runs all algorithms on the current job list."""
    from algorithms.scheduler import JobScheduler
    data = request.json or {}
    capacity = data.get("capacity")
    if capacity is not None:
        try:
            capacity = int(capacity)
        except ValueError:
            capacity = None

    jobs = get_all_jobs()
    comparison = JobScheduler.compare_all(jobs, capacity=capacity)
    return jsonify({"success": True, "comparison": comparison})


@app.route("/api/system-resources", methods=["GET", "POST"])
def api_system_resources():
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == "POST":
        data = request.json or {}
        cpu = max(1, int(data.get("total_cpu_cores", 8)))
        mem = max(1, int(data.get("total_memory_gb", 32)))
        cursor.execute("UPDATE system_resources SET total_cpu_cores = ?, total_memory_gb = ? WHERE id = 1", (cpu, mem))
        conn.commit()

    cursor.execute("SELECT * FROM system_resources WHERE id = 1")
    res = dict(cursor.fetchone() or {"total_cpu_cores": 8, "total_memory_gb": 32})
    conn.close()
    return jsonify({"success": True, "resources": res})


if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="127.0.0.1", port=5000)
