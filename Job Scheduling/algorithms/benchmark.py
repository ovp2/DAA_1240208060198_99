"""
Phase 6: Algorithm Benchmarking and Performance Analysis Service
Evaluates Greedy Algorithm vs. Dynamic Programming on identical datasets.
Ensures rigorous DAA empirical evaluation with repeated trials and high-resolution timing.
"""

import time
import random
import copy
from typing import List, Dict, Any, Tuple, Optional
from algorithms.greedy import greedy_job_scheduling
from algorithms.dynamic_programming import dynamic_programming_job_scheduling


def generate_benchmark_dataset(num_jobs: int, seed: int = 42) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Generates synthetic, deterministic benchmark datasets of jobs and resources.
    Guarantees the Fair Comparison Rule: Both algorithms receive identical jobs and resources.
    """
    rng = random.Random(seed + num_jobs)
    
    resource_types = ["Server", "Machine", "Employee", "Computer"]
    priorities = ["High", "Medium", "Low"]
    
    # Scale resources proportionally to dataset size
    num_resources = max(3, min(10, num_jobs // 10 + 2))
    resources = []
    for r_idx in range(1, num_resources + 1):
        res_type = resource_types[(r_idx - 1) % len(resource_types)]
        # Available hours scaled to ensure meaningful contention
        avail_hours = round(rng.uniform(18.0, 30.0), 1)
        resources.append({
            "id": r_idx,
            "resource_id": f"RES-{r_idx:02d}",
            "resource_name": f"{res_type} Cluster {r_idx}",
            "resource_type": res_type,
            "available_hours": avail_hours,
            "status": "Available"
        })
    
    # Generate jobs
    jobs = []
    # Maximum deadline scales with workload
    base_horizon = max(10, int(num_jobs * 1.2) + 5)
    
    for j_idx in range(1, num_jobs + 1):
        p_time = rng.randint(1, 6)
        # Ensure deadline is feasible relative to processing time
        dl = rng.randint(p_time + 1, base_horizon)
        profit = rng.randint(15, 250)
        pri = rng.choice(priorities)
        req_res = rng.choice(resource_types) if rng.random() > 0.2 else ""
        
        jobs.append({
            "id": j_idx,
            "job_id": j_idx,
            "name": f"Task-{j_idx:03d}",
            "job_name": f"Task-{j_idx:03d}",
            "processing_time": p_time,
            "burst_time": p_time,
            "deadline": dl,
            "profit": profit,
            "priority": pri,
            "required_resource": req_res,
            "status": "Pending"
        })
        
    return jobs, resources


def run_benchmark_comparison(
    dataset_size: str = "small",
    custom_count: Optional[int] = None,
    repeat_runs: int = 5,
    conn = None
) -> Dict[str, Any]:
    """
    Executes a head-to-head empirical comparison between Greedy and Dynamic Programming.
    
    Parameters:
      - dataset_size: 'small' (10), 'medium' (50), 'large' (100), 'extra_large' (500), 'custom'
      - custom_count: integer job count when dataset_size == 'custom'
      - repeat_runs: number of repeated trials for timing reliability (default: 5)
      - conn: SQLite connection to persist benchmark results into benchmark_results table
    """
    size_map = {
        "small": 10,
        "medium": 50,
        "large": 100,
        "extra_large": 500,
        "extra large": 500,
        "xlarge": 500
    }
    
    num_jobs = 0
    if dataset_size in size_map:
        num_jobs = size_map[dataset_size]
    elif dataset_size == "custom":
        if custom_count is None:
            return {
                "success": False,
                "error": "Custom dataset size requires a specific job count."
            }
        try:
            num_jobs = int(custom_count)
        except (ValueError, TypeError):
            return {
                "success": False,
                "error": "Invalid custom job count. Must be a positive integer."
            }
    else:
        return {
            "success": False,
            "error": f"Invalid dataset size '{dataset_size}'. Must be 'small', 'medium', 'large', 'extra_large', or 'custom'."
        }
        
    if num_jobs <= 0:
        return {
            "success": False,
            "error": "Dataset size must contain at least 1 job."
        }
    if num_jobs > 1000:
        return {
            "success": False,
            "error": "Dataset size exceeds maximum allowable limit (1000 jobs)."
        }
        
    repeat_runs = max(1, min(10, int(repeat_runs)))

    # 2. Generate isolated dataset (Requirement 24: Data Safety - does not touch user's DB jobs)
    base_jobs, base_resources = generate_benchmark_dataset(num_jobs)
    total_resource_hours = sum(r["available_hours"] for r in base_resources)

    # -------------------------------------------------------------------------
    # 3. BENCHMARK GREEDY ALGORITHM
    # -------------------------------------------------------------------------
    greedy_times = []
    greedy_last_res = None
    
    for _ in range(repeat_runs):
        jobs_copy = copy.deepcopy(base_jobs)
        res_copy = copy.deepcopy(base_resources)
        
        t0 = time.perf_counter()
        greedy_res = greedy_job_scheduling(jobs_copy, res_copy)
        t_elapsed = time.perf_counter() - t0
        greedy_times.append(t_elapsed)
        greedy_last_res = greedy_res

    greedy_avg_time = round(sum(greedy_times) / len(greedy_times), 6)
    greedy_min_time = round(min(greedy_times), 6)
    greedy_max_time = round(max(greedy_times), 6)

    greedy_m = greedy_last_res["metrics"]
    greedy_sched_count = greedy_m["scheduled_count"]
    greedy_missed_count = greedy_m["missed_count"]
    greedy_profit = greedy_m["total_profit"]
    greedy_proc_time = greedy_m.get("used_resource_hours", 0.0)
    greedy_util = greedy_m.get("resource_utilization", 0.0)
    
    if greedy_sched_count > 0:
        greedy_deadline_success = f"{greedy_m.get('on_time_rate', greedy_m.get('deadline_success_rate', 100.0))}%"
        greedy_deadline_val = float(greedy_m.get("on_time_rate", greedy_m.get("deadline_success_rate", 100.0)))
    else:
        greedy_deadline_success = "N/A"
        greedy_deadline_val = 0.0

    # -------------------------------------------------------------------------
    # 4. BENCHMARK DYNAMIC PROGRAMMING ALGORITHM
    # -------------------------------------------------------------------------
    # DP Capacity Safety Check (Requirements 7 & 26):
    # Calculate DP state space N * T. If N >= 500 or N * T > 300,000,
    # skip DP gracefully and display friendly message rather than crashing.
    max_dl = max(j["deadline"] for j in base_jobs) if base_jobs else 0
    sum_p = sum(j["processing_time"] for j in base_jobs) if base_jobs else 0
    T_cap = int(min(max_dl, sum_p, total_resource_hours))
    dp_state_space = num_jobs * T_cap

    dp_exceeded = False
    dp_exceeded_message = ""
    dp_times = []
    dp_last_res = None

    if num_jobs >= 500 or dp_state_space > 300000:
        dp_exceeded = True
        dp_exceeded_message = (
            f"Dataset exceeds the practical DP demonstration limit (N={num_jobs}, T={T_cap}, "
            f"states={dp_state_space:,}). Dynamic Programming was safely bypassed to prevent "
            f"excessive memory allocation while highlighting asymptotic scalability limits."
        )
        dp_avg_time = None
        dp_min_time = None
        dp_max_time = None
        dp_sched_count = "N/A"
        dp_missed_count = "N/A"
        dp_profit = "N/A"
        dp_proc_time = "N/A"
        dp_util = "N/A"
        dp_deadline_success = "N/A"
        dp_deadline_val = 0.0
    else:
        for _ in range(repeat_runs):
            jobs_copy = copy.deepcopy(base_jobs)
            res_copy = copy.deepcopy(base_resources)
            
            t0 = time.perf_counter()
            dp_res = dynamic_programming_job_scheduling(jobs_copy, res_copy)
            t_elapsed = time.perf_counter() - t0
            dp_times.append(t_elapsed)
            dp_last_res = dp_res

        dp_avg_time = round(sum(dp_times) / len(dp_times), 6)
        dp_min_time = round(min(dp_times), 6)
        dp_max_time = round(max(dp_times), 6)

        dp_m = dp_last_res["metrics"]
        dp_sched_count = dp_m["scheduled_count"]
        dp_missed_count = dp_m["missed_count"]
        dp_profit = dp_m["total_profit"]
        dp_proc_time = dp_m.get("total_processing_time", dp_m.get("used_resource_hours", 0.0))
        dp_util = dp_m.get("resource_utilization", 0.0)
        
        if dp_sched_count > 0:
            dp_deadline_success = f"{dp_m.get('on_time_rate', dp_m.get('deadline_success_rate', 100.0))}%"
            dp_deadline_val = float(dp_m.get("on_time_rate", dp_m.get("deadline_success_rate", 100.0)))
        else:
            dp_deadline_success = "N/A"
            dp_deadline_val = 0.0

    # -------------------------------------------------------------------------
    # 5. PERSIST BENCHMARK RESULTS IN DATABASE (Requirement 9)
    # -------------------------------------------------------------------------
    if conn:
        try:
            cursor = conn.cursor()
            # Store Greedy run
            cursor.execute("""
                INSERT INTO benchmark_results (
                    dataset_size, num_jobs, algorithm, execution_time,
                    min_execution_time, max_execution_time, jobs_scheduled,
                    jobs_missed, total_profit, processing_time,
                    resource_utilization, deadline_success_rate
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                dataset_size, num_jobs, "Greedy", greedy_avg_time,
                greedy_min_time, greedy_max_time, greedy_sched_count,
                greedy_missed_count, greedy_profit, greedy_proc_time,
                greedy_util, greedy_deadline_val
            ))
            
            # Store DP run if not exceeded
            if not dp_exceeded:
                cursor.execute("""
                    INSERT INTO benchmark_results (
                        dataset_size, num_jobs, algorithm, execution_time,
                        min_execution_time, max_execution_time, jobs_scheduled,
                        jobs_missed, total_profit, processing_time,
                        resource_utilization, deadline_success_rate
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    dataset_size, num_jobs, "Dynamic Programming", dp_avg_time,
                    dp_min_time, dp_max_time, dp_sched_count,
                    dp_missed_count, dp_profit, dp_proc_time,
                    dp_util, dp_deadline_val
                ))
            conn.commit()
        except Exception as e:
            # Non-fatal log
            print(f"[Benchmark DB Log Error]: {e}")

    # -------------------------------------------------------------------------
    # 6. FORMULATE FACTUAL EXPERIMENTAL SUMMARY (Requirement 16)
    # -------------------------------------------------------------------------
    observations = [
        f"Evaluated {num_jobs} jobs with {len(base_resources)} resources across {repeat_runs} timed iterations.",
        f"Greedy completed in an average of {greedy_avg_time:.6f}s (min: {greedy_min_time:.6f}s, max: {greedy_max_time:.6f}s), scheduling {greedy_sched_count} jobs and achieving ${greedy_profit} total profit."
    ]
    if dp_exceeded:
        observations.append(
            f"Dynamic Programming: {dp_exceeded_message}"
        )
    else:
        observations.append(
            f"Dynamic Programming completed in an average of {dp_avg_time:.6f}s (min: {dp_min_time:.6f}s, max: {dp_max_time:.6f}s), scheduling {dp_sched_count} jobs and achieving ${dp_profit} total profit."
        )
        if dp_profit > greedy_profit:
            observations.append(
                f"For this dataset, Dynamic Programming achieved ${dp_profit - greedy_profit} higher profit by evaluating overlapping multi-job combinations rather than single greedy steps."
            )
        elif dp_profit == greedy_profit:
            observations.append(
                "Both algorithms achieved identical total profit on this dataset."
            )
        else:
            observations.append(
                f"Greedy achieved higher profit on this dataset by prioritized immediate allocation."
            )

    return {
        "success": True,
        "dataset_size": dataset_size,
        "num_jobs": num_jobs,
        "num_resources": len(base_resources),
        "total_resource_hours": round(total_resource_hours, 1),
        "repeat_runs": repeat_runs,
        "dp_exceeded": dp_exceeded,
        "dp_exceeded_message": dp_exceeded_message,
        "greedy": {
            "name": "Greedy Algorithm",
            "avg_execution_time": greedy_avg_time,
            "min_execution_time": greedy_min_time,
            "max_execution_time": greedy_max_time,
            "jobs_scheduled": greedy_sched_count,
            "jobs_missed": greedy_missed_count,
            "total_profit": greedy_profit,
            "total_processing_time": greedy_proc_time,
            "resource_utilization": greedy_util,
            "deadline_success_rate": greedy_deadline_success,
            "time_complexity": "O(N log N + N × M)",
            "space_complexity": "O(N + M)"
        },
        "dynamic_programming": {
            "name": "Dynamic Programming",
            "avg_execution_time": dp_avg_time,
            "min_execution_time": dp_min_time,
            "max_execution_time": dp_max_time,
            "jobs_scheduled": dp_sched_count,
            "jobs_missed": dp_missed_count,
            "total_profit": dp_profit,
            "total_processing_time": dp_proc_time,
            "resource_utilization": dp_util,
            "deadline_success_rate": dp_deadline_success,
            "time_complexity": "O(N × ∏ C_r) exact / O(N × T) grid",
            "space_complexity": "O(N × ∏ C_r) exact / O(N × T) grid",
            "scheduling_capacity": T_cap,
            "exceeded_limit": dp_exceeded,
            "message": dp_exceeded_message
        },
        "dp": {
            "name": "Dynamic Programming",
            "avg_execution_time": dp_avg_time,
            "min_execution_time": dp_min_time,
            "max_execution_time": dp_max_time,
            "jobs_scheduled": dp_sched_count,
            "jobs_missed": dp_missed_count,
            "total_profit": dp_profit,
            "total_processing_time": dp_proc_time,
            "resource_utilization": dp_util,
            "deadline_success_rate": dp_deadline_success,
            "time_complexity": "O(N × ∏ C_r) exact / O(N × T) grid",
            "space_complexity": "O(N × ∏ C_r) exact / O(N × T) grid",
            "scheduling_capacity": T_cap,
            "exceeded_limit": dp_exceeded,
            "message": dp_exceeded_message
        },
        "observations": observations
    }


def get_multi_size_benchmark_trend(repeat_runs: int = 3) -> Dict[str, Any]:
    """
    Generates multi-point scalability data across Small (10), Medium (50), Large (100), and Extra Large (500)
    for rendering the execution time vs dataset size chart.
    """
    test_sizes = [("Small (10)", 10), ("Medium (50)", 50), ("Large (100)", 100), ("XL (500)", 500)]
    labels = []
    greedy_series = []
    dp_series = []
    
    for label, count in test_sizes:
        res = run_benchmark_comparison(
            dataset_size="custom" if count not in [10, 50, 100] else ("small" if count == 10 else ("medium" if count == 50 else "large")),
            custom_count=count,
            repeat_runs=repeat_runs
        )
        labels.append(label)
        greedy_series.append(res["greedy"]["avg_execution_time"])
        if res["dp_exceeded"] or res["dynamic_programming"]["avg_execution_time"] is None:
            dp_series.append(None)
        else:
            dp_series.append(res["dynamic_programming"]["avg_execution_time"])
            
    return {
        "labels": labels,
        "greedy_times": greedy_series,
        "dp_times": dp_series
    }
