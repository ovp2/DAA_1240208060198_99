"""
Unified Job Scheduler Engine
Acts as an orchestrator for all greedy and dynamic programming scheduling algorithms.
Computes comprehensive metrics, timeline breakdowns, and multi-algorithm comparisons.
"""

from typing import List, Dict, Any, Optional
from algorithms.greedy import (
    fcfs_schedule,
    sjf_schedule,
    priority_schedule,
    edf_schedule,
    job_sequencing_with_deadlines,
    greedy_job_scheduling
)
from algorithms.dynamic_programming import (
    weighted_interval_scheduling,
    knapsack_job_scheduling,
    dynamic_programming_job_scheduling
)

# Canonical list of supported algorithms
ALGORITHMS_REGISTRY = {
    "fcfs": {
        "name": "First-Come, First-Served (FCFS)",
        "category": "Greedy",
        "description": "Executes jobs strictly in arrival order. Non-preemptive, simple, zero starvation.",
        "preemptive": False
    },
    "sjf": {
        "name": "Shortest Job First (SJF)",
        "category": "Greedy",
        "description": "Selects the available job with the shortest execution burst. Optimal average waiting time for non-preemptive.",
        "preemptive": False
    },
    "srtf": {
        "name": "Shortest Remaining Time First (SRTF)",
        "category": "Greedy",
        "description": "Preemptive version of SJF. Preempts current job when a shorter job arrives.",
        "preemptive": True
    },
    "priority_np": {
        "name": "Priority Scheduling (Non-Preemptive)",
        "category": "Greedy",
        "description": "Schedules highest priority job (lowest numeric level) among ready tasks without interruption.",
        "preemptive": False
    },
    "priority_p": {
        "name": "Priority Scheduling (Preemptive)",
        "category": "Greedy",
        "description": "Preemptively interrupts execution whenever a strictly higher priority job arrives.",
        "preemptive": True
    },
    "edf_np": {
        "name": "Earliest Deadline First (EDF - Non-Preemptive)",
        "category": "Greedy / Real-Time",
        "description": "Prioritizes tasks with imminent deadlines to minimize tardiness.",
        "preemptive": False
    },
    "edf_p": {
        "name": "Earliest Deadline First (EDF - Preemptive)",
        "category": "Greedy / Real-Time",
        "description": "Dynamic priority real-time scheduling algorithm with preemption on tighter deadlines.",
        "preemptive": True
    },
    "job_sequencing": {
        "name": "Job Sequencing with Deadlines",
        "category": "Greedy",
        "description": "Greedy strategy sorting jobs by profit and booking the latest available slot before deadline.",
        "preemptive": False
    },
    "dp_interval": {
        "name": "Weighted Interval Scheduling (DP)",
        "category": "Dynamic Programming",
        "description": "Exact optimal subset selection using O(n log n) dynamic programming and binary search.",
        "preemptive": False
    },
    "dp_knapsack": {
        "name": "0/1 Knapsack Job Selection (DP)",
        "category": "Dynamic Programming",
        "description": "Maximizes total profit within a bounded execution budget using 2D Dynamic Programming.",
        "preemptive": False
    }
}


class JobScheduler:
    """Unified Facade for scheduling algorithms and metrics generation."""

    @staticmethod
    def run_algorithm(algo_key: str, jobs: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """
        Executes a scheduling algorithm by key and returns enriched metrics and timeline.
        """
        if not jobs:
            return {
                "algorithm_key": algo_key,
                "algorithm_name": ALGORITHMS_REGISTRY.get(algo_key, {}).get("name", algo_key),
                "timeline": [],
                "job_results": [],
                "metrics": JobScheduler._empty_metrics(),
                "error": "No jobs provided for scheduling."
            }

        algo_info = ALGORITHMS_REGISTRY.get(algo_key, {
            "name": algo_key,
            "category": "Custom",
            "preemptive": False
        })

        # Dispatch
        raw_result = {}
        if algo_key == "fcfs":
            raw_result = fcfs_schedule(jobs)
        elif algo_key == "sjf":
            raw_result = sjf_schedule(jobs, preemptive=False)
        elif algo_key == "srtf":
            raw_result = sjf_schedule(jobs, preemptive=True)
        elif algo_key == "priority_np":
            raw_result = priority_schedule(jobs, preemptive=False)
        elif algo_key == "priority_p":
            raw_result = priority_schedule(jobs, preemptive=True)
        elif algo_key == "edf_np":
            raw_result = edf_schedule(jobs, preemptive=False)
        elif algo_key == "edf_p":
            raw_result = edf_schedule(jobs, preemptive=True)
        elif algo_key == "job_sequencing":
            raw_result = job_sequencing_with_deadlines(jobs)
        elif algo_key == "dp_interval":
            raw_result = weighted_interval_scheduling(jobs)
        elif algo_key == "dp_knapsack":
            capacity = kwargs.get("capacity")
            raw_result = knapsack_job_scheduling(jobs, capacity=capacity)
        else:
            raw_result = fcfs_schedule(jobs)

        timeline = raw_result.get("timeline", [])
        job_results = raw_result.get("job_results", [])
        metrics = JobScheduler.compute_metrics(jobs, timeline, job_results)

        # Resource utilization series
        resource_series = JobScheduler.compute_resource_usage(timeline, jobs)

        return {
            "algorithm_key": algo_key,
            "algorithm_name": algo_info["name"],
            "category": algo_info.get("category", "General"),
            "description": algo_info.get("description", ""),
            "preemptive": algo_info.get("preemptive", False),
            "timeline": timeline,
            "job_results": job_results,
            "metrics": metrics,
            "resource_series": resource_series,
            "dp_table": raw_result.get("dp_table", []),
            "dp_grid": raw_result.get("dp_grid", None),
            "capacity": raw_result.get("capacity", None)
        }

    @staticmethod
    def compare_all(jobs: List[Dict[str, Any]], capacity: Optional[int] = None) -> Dict[str, Any]:
        """
        Runs all registered algorithms on the input jobs and generates comparative benchmarks.
        """
        comparison_results = []
        for key in ALGORITHMS_REGISTRY.keys():
            res = JobScheduler.run_algorithm(key, jobs, capacity=capacity)
            comparison_results.append({
                "key": key,
                "name": res["algorithm_name"],
                "category": res["category"],
                "metrics": res["metrics"],
                "timeline": res["timeline"]
            })

        # Identify benchmark leaders
        valid_results = [r for r in comparison_results if r["metrics"]["makespan"] > 0]
        
        best_waiting_time = None
        best_turnaround_time = None
        highest_profit = None
        highest_cpu_util = None
        most_deadlines_met = None

        if valid_results:
            best_waiting_time = min(valid_results, key=lambda r: r["metrics"]["avg_waiting_time"])
            best_turnaround_time = min(valid_results, key=lambda r: r["metrics"]["avg_turnaround_time"])
            highest_profit = max(valid_results, key=lambda r: r["metrics"]["total_profit"])
            highest_cpu_util = max(valid_results, key=lambda r: r["metrics"]["cpu_utilization"])
            most_deadlines_met = max(valid_results, key=lambda r: r["metrics"]["deadlines_met"])

        return {
            "algorithms": comparison_results,
            "winners": {
                "lowest_avg_waiting_time": {
                    "algorithm": best_waiting_time["name"] if best_waiting_time else "N/A",
                    "value": best_waiting_time["metrics"]["avg_waiting_time"] if best_waiting_time else 0
                },
                "lowest_avg_turnaround_time": {
                    "algorithm": best_turnaround_time["name"] if best_turnaround_time else "N/A",
                    "value": best_turnaround_time["metrics"]["avg_turnaround_time"] if best_turnaround_time else 0
                },
                "highest_profit": {
                    "algorithm": highest_profit["name"] if highest_profit else "N/A",
                    "value": highest_profit["metrics"]["total_profit"] if highest_profit else 0
                },
                "highest_cpu_utilization": {
                    "algorithm": highest_cpu_util["name"] if highest_cpu_util else "N/A",
                    "value": highest_cpu_util["metrics"]["cpu_utilization"] if highest_cpu_util else 0
                },
                "most_deadlines_met": {
                    "algorithm": most_deadlines_met["name"] if most_deadlines_met else "N/A",
                    "value": f"{most_deadlines_met['metrics']['deadlines_met']} / {most_deadlines_met['metrics']['total_jobs']}" if most_deadlines_met else "0/0"
                }
            }
        }

    @staticmethod
    def compute_metrics(original_jobs: List[Dict[str, Any]], timeline: List[Dict[str, Any]], job_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculates performance indicators."""
        total_jobs = len(original_jobs)
        if total_jobs == 0:
            return JobScheduler._empty_metrics()

        makespan = max((t["end"] for t in timeline), default=0)
        busy_time = sum(t["duration"] for t in timeline if t["type"] == "job")
        idle_time = sum(t["duration"] for t in timeline if t["type"] == "idle")

        cpu_utilization = round((busy_time / makespan * 100), 2) if makespan > 0 else 0.0

        # Filter jobs that were actually executed
        executed_jobs = [j for j in job_results if j.get("start_time") is not None]
        scheduled_count = len(executed_jobs)
        rejected_count = total_jobs - scheduled_count

        total_profit = sum(j["profit"] for j in executed_jobs)
        total_waiting_time = sum(j["waiting_time"] for j in executed_jobs)
        total_turnaround_time = sum(j["turnaround_time"] for j in executed_jobs)
        total_tardiness = sum(j.get("tardiness", 0) for j in executed_jobs)
        deadlines_met = sum(1 for j in executed_jobs if j.get("met_deadline", False))

        avg_waiting_time = round(total_waiting_time / scheduled_count, 2) if scheduled_count > 0 else 0.0
        avg_turnaround_time = round(total_turnaround_time / scheduled_count, 2) if scheduled_count > 0 else 0.0
        avg_tardiness = round(total_tardiness / scheduled_count, 2) if scheduled_count > 0 else 0.0
        deadline_compliance_rate = round((deadlines_met / total_jobs * 100), 1) if total_jobs > 0 else 0.0
        throughput = round(scheduled_count / makespan, 3) if makespan > 0 else 0.0

        return {
            "total_jobs": total_jobs,
            "scheduled_jobs": scheduled_count,
            "rejected_jobs": rejected_count,
            "makespan": makespan,
            "busy_time": busy_time,
            "idle_time": idle_time,
            "cpu_utilization": cpu_utilization,
            "total_profit": total_profit,
            "avg_waiting_time": avg_waiting_time,
            "avg_turnaround_time": avg_turnaround_time,
            "avg_tardiness": avg_tardiness,
            "deadlines_met": deadlines_met,
            "deadline_compliance_rate": deadline_compliance_rate,
            "throughput": throughput
        }

    @staticmethod
    def compute_resource_usage(timeline: List[Dict[str, Any]], original_jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generates timeline steps of CPU and Memory consumption.
        """
        job_map = {j["id"]: j for j in original_jobs}
        time_points = set([0])
        for item in timeline:
            time_points.add(item["start"])
            time_points.add(item["end"])

        sorted_points = sorted(time_points)
        series = []

        for t in sorted_points:
            active_items = [item for item in timeline if item["start"] <= t < item["end"] and item["type"] == "job"]
            cpu_used = 0
            mem_used = 0
            for item in active_items:
                orig = job_map.get(item["job_id"], {})
                cpu_used += orig.get("cpu_req", 1)
                mem_used += orig.get("mem_req", 2)

            series.append({
                "time": t,
                "cpu_cores": cpu_used,
                "memory_gb": mem_used,
                "active_job": active_items[0]["job_name"] if active_items else "Idle"
            })

        return series

    @staticmethod
    def _empty_metrics() -> Dict[str, Any]:
        return {
            "total_jobs": 0,
            "scheduled_jobs": 0,
            "rejected_jobs": 0,
            "makespan": 0,
            "busy_time": 0,
            "idle_time": 0,
            "cpu_utilization": 0.0,
            "total_profit": 0,
            "avg_waiting_time": 0.0,
            "avg_turnaround_time": 0.0,
            "avg_tardiness": 0.0,
            "deadlines_met": 0,
            "deadline_compliance_rate": 0.0,
            "throughput": 0.0
        }


# =========================================================================
# PHASE 4 SCHEDULER SERVICE LAYER
# =========================================================================

def run_greedy_scheduler_service(conn) -> Dict[str, Any]:
    """
    Executes Phase 4 Greedy Scheduling:
    1. Reads candidate jobs from database.
    2. Reads available resources.
    3. Calls greedy_job_scheduling().
    4. Saves successfully scheduled jobs into schedules table.
    5. Updates job records with status ('Scheduled' or 'Missed') and specific missed_reason.
    6. Returns execution telemetry, metrics, and logs.
    """
    cursor = conn.cursor()

    # 1. Fetch candidate jobs (non-completed jobs)
    cursor.execute("""
        SELECT * FROM jobs 
        WHERE status != 'Completed'
        ORDER BY arrival_time ASC, id ASC
    """)
    candidate_rows = cursor.fetchall()
    jobs = [dict(r) for r in candidate_rows]

    # 2. Fetch available resources
    cursor.execute("""
        SELECT * FROM resources 
        WHERE status = 'Available'
        ORDER BY id ASC
    """)
    res_rows = cursor.fetchall()
    resources = [dict(r) for r in res_rows]

    if not jobs:
        return {
            "success": False,
            "message": "No candidate jobs found in database to schedule. Please add jobs first.",
            "metrics": {
                "total_jobs": 0,
                "scheduled_count": 0,
                "missed_count": 0,
                "total_profit": 0.0,
                "total_processing_time": 0.0,
                "resource_utilization": 0.0,
                "deadline_success_rate": 0.0,
                "on_time_rate": 0.0,
                "on_time_count": 0,
                "total_resource_hours": 0.0,
                "used_resource_hours": 0.0
            },
            "scheduled_jobs": [],
            "missed_jobs": [],
            "schedules": [],
            "execution_time": 0.0,
            "num_jobs": 0,
            "num_resources": len(resources),
            "step_by_step_log": []
        }

    # Clear previous active schedule records
    cursor.execute("DELETE FROM schedules")

    # 3. Execute Greedy Algorithm
    res = greedy_job_scheduling(jobs, resources)

    # 4. Save results to schedules table
    for s in res["schedules"]:
        cursor.execute("""
            INSERT INTO schedules (
                job_id, job_name, processing_time, deadline,
                start_time, end_time, resource_id, resource_name,
                profit, priority, status, algorithm
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            s["job_id"],
            s["job_name"],
            s["processing_time"],
            s["deadline"],
            s["start_time"],
            s["end_time"],
            s["resource_id"],
            s["resource_name"],
            s["profit"],
            s["priority"],
            s["status"],
            s["algorithm"]
        ))

    # 5. Update job statuses and missed_reason in jobs table
    for s in res["scheduled_jobs"]:
        cursor.execute("""
            UPDATE jobs 
            SET status = 'Scheduled', assigned_resource_id = ?, missed_reason = '' 
            WHERE id = ?
        """, (s["assigned_resource_id"], s["id"]))

    for m in res["missed_jobs"]:
        reason_str = m.get("missed_reason", "NO_FEASIBLE_SLOT: Could not place on compatible resources.")
        cursor.execute("""
            UPDATE jobs 
            SET status = 'Missed', assigned_resource_id = NULL, missed_reason = ? 
            WHERE id = ?
        """, (reason_str, m["id"]))

    # Record run in execution_history
    cursor.execute("""
        INSERT INTO execution_history (
            algorithm_name, algorithm_key, total_jobs, makespan,
            avg_waiting_time, avg_turnaround_time, total_profit, cpu_utilization
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "Greedy Job Scheduling",
        "greedy_daa",
        res["metrics"]["total_jobs"],
        max((s["end_time"] for s in res["schedules"]), default=0),
        res["execution_time"],
        0.0,
        res["metrics"]["total_profit"],
        res["metrics"]["resource_utilization"]
    ))

    conn.commit()

    res["success"] = True
    res["message"] = f"Greedy Algorithm executed successfully: {res['metrics']['scheduled_count']} scheduled, {res['metrics']['missed_count']} missed (Total Profit: ${res['metrics']['total_profit']})."
    return res


# ==============================================================================
# PHASE 5: DYNAMIC PROGRAMMING SCHEDULER SERVICE
# ==============================================================================

def run_dp_scheduler_service(conn) -> Dict[str, Any]:
    """
    Phase 5 Database Integration Service for Dynamic Programming:
    1. Fetches candidate jobs (non-completed jobs).
    2. Fetches active available resources.
    3. Executes dynamic_programming_job_scheduling().
    4. Saves reconstructed selected jobs into the 'schedules' table with algorithm='Dynamic Programming'.
    5. Updates job records in 'jobs' table (Scheduled or Missed with specific missed_reason).
    6. Logs execution metrics and timing in 'execution_history'.
    """
    cursor = conn.cursor()

    # 1. Fetch candidate jobs
    cursor.execute("""
        SELECT * FROM jobs 
        WHERE status != 'Completed'
        ORDER BY arrival_time ASC, id ASC
    """)
    jobs = [dict(r) for r in cursor.fetchall()]

    # 2. Fetch available resources
    cursor.execute("SELECT * FROM resources WHERE status = 'Available' ORDER BY id ASC")
    resources = [dict(r) for r in cursor.fetchall()]

    if not jobs:
        return {
            "success": False,
            "message": "No jobs found in database to schedule. Please add jobs first.",
            "metrics": {
                "total_jobs": 0,
                "scheduled_count": 0,
                "missed_count": 0,
                "total_profit": 0,
                "total_processing_time": 0,
                "resource_utilization": 0.0,
                "deadline_success_rate": 0.0,
                "on_time_rate": 0.0,
                "on_time_count": 0,
                "total_resource_hours": 0.0,
                "used_resource_hours": 0.0
            },
            "schedules": [],
            "scheduled_jobs": [],
            "missed_jobs": [],
            "execution_time": 0.0,
            "num_jobs": 0,
            "scheduling_capacity": 0,
            "dp_grid": {"is_visualizable": False, "message": "No jobs to schedule."}
        }

    # Clear previous active schedule records
    cursor.execute("DELETE FROM schedules")

    # 3. Execute Dynamic Programming Algorithm
    res = dynamic_programming_job_scheduling(jobs, resources)

    # 4. Save results to schedules table
    for s in res["schedules"]:
        cursor.execute("""
            INSERT INTO schedules (
                job_id, job_name, processing_time, deadline,
                start_time, end_time, resource_id, resource_name,
                profit, priority, status, algorithm
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            s["job_id"],
            s["job_name"],
            s["processing_time"],
            s["deadline"],
            s["start_time"],
            s["end_time"],
            s["resource_id"],
            s["resource_name"],
            s["profit"],
            s["priority"],
            s["status"],
            s["algorithm"]
        ))

    # 5. Update job statuses and missed_reason in jobs table
    for s in res["scheduled_jobs"]:
        cursor.execute("""
            UPDATE jobs 
            SET status = 'Scheduled', assigned_resource_id = ?, missed_reason = '' 
            WHERE id = ?
        """, (s["assigned_resource_id"], s["id"]))

    for m in res["missed_jobs"]:
        reason_str = m.get("missed_reason", "NOT_SELECTED_BY_OPTIMIZER: Omitted by DP optimizer.")
        cursor.execute("""
            UPDATE jobs 
            SET status = 'Missed', assigned_resource_id = NULL, missed_reason = ? 
            WHERE id = ?
        """, (reason_str, m["id"]))

    # 6. Record run in execution_history
    cursor.execute("""
        INSERT INTO execution_history (
            algorithm_name, algorithm_key, total_jobs, makespan,
            avg_waiting_time, avg_turnaround_time, total_profit, cpu_utilization
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "Dynamic Programming Job Scheduling",
        "dp_daa",
        res["metrics"]["total_jobs"],
        max((s["end_time"] for s in res["schedules"]), default=0),
        res["execution_time"],
        res["scheduling_capacity"],
        res["metrics"]["total_profit"],
        res["metrics"]["resource_utilization"]
    ))

    conn.commit()

    res["success"] = True
    res["message"] = f"Dynamic Programming executed successfully: {res['metrics']['scheduled_count']} scheduled, {res['metrics']['missed_count']} missed (Total Profit: ${res['metrics']['total_profit']})."
    return res


def reset_schedule_service(conn) -> Dict[str, Any]:
    """
    Resets the schedule:
    1. Deletes all generated schedule records.
    2. Resets jobs from 'Scheduled' or 'Missed' back to 'Pending'.
    3. Clears assigned_resource_id and missed_reason on jobs.
    Does NOT delete jobs or resources.
    Supports resetting schedules generated by both Greedy and Dynamic Programming.
    """
    cursor = conn.cursor()
    cursor.execute("DELETE FROM schedules")
    cursor.execute("""
        UPDATE jobs 
        SET status = 'Pending', assigned_resource_id = NULL, missed_reason = '' 
        WHERE status IN ('Scheduled', 'Missed')
    """)
    conn.commit()

    return {
        "success": True,
        "message": "Schedule reset successfully. All jobs restored to 'Pending' and schedules cleared."
    }


def get_current_schedule_service(conn) -> Dict[str, Any]:
    """
    Retrieves the current schedule records, missed jobs, and summary statistics.
    Identifies whether the current active schedule was produced by Greedy or Dynamic Programming.
    """
    cursor = conn.cursor()

    # Get active schedules
    cursor.execute("SELECT * FROM schedules ORDER BY start_time ASC, id ASC")
    schedules = [dict(r) for r in cursor.fetchall()]

    # Get missed jobs
    cursor.execute("SELECT * FROM jobs WHERE status = 'Missed' ORDER BY id ASC")
    missed = [dict(r) for r in cursor.fetchall()]

    # Identify algorithm used
    algorithm_used = "Greedy"
    if schedules:
        algorithm_used = schedules[0].get("algorithm") or "Greedy"
    else:
        # Check latest execution history run
        cursor.execute("SELECT algorithm_name, algorithm_key FROM execution_history ORDER BY id DESC LIMIT 1")
        last_hist = cursor.fetchone()
        if last_hist and "Dynamic Programming" in last_hist["algorithm_name"]:
            algorithm_used = "Dynamic Programming"

    # Calculate real statistics
    scheduled_count = len(schedules)
    missed_count = len(missed)
    total_jobs = scheduled_count + missed_count
    total_profit = sum(s["profit"] for s in schedules)
    total_processing_time = sum(s["processing_time"] for s in schedules)

    # Resource capacity and utilization
    cursor.execute("SELECT * FROM resources WHERE status = 'Available' ORDER BY id ASC")
    res_rows = [dict(r) for r in cursor.fetchall()]
    total_resource_hours = sum(float(r.get("available_hours", 0.0)) for r in res_rows)
    resource_count = len(res_rows)

    used_resource_hours = total_processing_time
    utilization_pct = round((used_resource_hours / total_resource_hours * 100.0), 2) if total_resource_hours > 0 else 0.0

    # On-time completion rate: jobs completed by deadline / scheduled jobs * 100
    on_time_count = sum(1 for s in schedules if s["end_time"] <= s["deadline"])
    on_time_rate = round((on_time_count / scheduled_count * 100.0), 2) if scheduled_count > 0 else 0.0

    # Timeline horizon (T_max): latest deadline across all jobs in system
    cursor.execute("SELECT MAX(deadline) FROM jobs")
    max_dl_val = cursor.fetchone()[0]
    timeline_horizon = float(max_dl_val) if max_dl_val is not None else 11.0

    # Elapsed schedule duration (makespan): wall-clock elapsed time from first start to last finish
    if schedules:
        earliest_start = min(s["start_time"] for s in schedules)
        latest_finish = max(s["end_time"] for s in schedules)
        elapsed_schedule_duration = round(max(0.0, latest_finish - earliest_start), 2)
        makespan = round(latest_finish, 2)
    else:
        earliest_start = 0.0
        latest_finish = 0.0
        elapsed_schedule_duration = 0.0
        makespan = 0.0

    # Validate schedule against all 8 operational constraints
    cursor.execute("SELECT * FROM jobs ORDER BY id ASC")
    all_jobs_raw = [dict(r) for r in cursor.fetchall()]
    from algorithms.dynamic_programming import validate_schedule
    validation_res = validate_schedule(schedules, res_rows, all_jobs_raw) if schedules else {"valid": True, "error": None}

    return {
        "schedules": schedules,
        "missed_jobs": missed,
        "algorithm_used": algorithm_used,
        "metrics": {
            "total_jobs": total_jobs,
            "scheduled_count": scheduled_count,
            "missed_count": missed_count,
            "total_profit": total_profit,
            "total_processing_time": total_processing_time,
            "makespan": makespan,
            "elapsed_schedule_duration": elapsed_schedule_duration,
            "timeline_horizon": timeline_horizon,
            "resource_count": resource_count,
            "resource_utilization": utilization_pct,
            "deadline_success_rate": on_time_rate,
            "on_time_rate": on_time_rate,
            "on_time_count": on_time_count,
            "total_resource_hours": round(total_resource_hours, 2),
            "used_resource_hours": round(used_resource_hours, 2),
            "is_valid": validation_res.get("valid", False),
            "validation_error": validation_res.get("error", None)
        }
    }

