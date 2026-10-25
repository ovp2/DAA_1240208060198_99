"""
Greedy Job Scheduling Algorithms
Includes:
- First-Come, First-Served (FCFS)
- Shortest Job First (SJF - Non-Preemptive)
- Shortest Remaining Time First (SRTF - Preemptive SJF)
- Priority Scheduling (Non-Preemptive & Preemptive)
- Earliest Deadline First (EDF)
- Job Sequencing with Deadlines (Profit Maximization)
- Multi-Resource Greedy Scheduling
"""

from typing import List, Dict, Any


def fcfs_schedule(jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    First-Come, First-Served (FCFS) Scheduling.
    Executes jobs in order of arrival time. Non-preemptive.
    """
    if not jobs:
        return {"timeline": [], "job_results": [], "metrics": {}}

    # Sort jobs by arrival time, then by ID
    sorted_jobs = sorted(jobs, key=lambda j: (j["arrival_time"], j["id"]))
    
    current_time = 0
    timeline = []
    job_results = []
    
    for job in sorted_jobs:
        arrival = job["arrival_time"]
        burst = job["burst_time"]
        
        # CPU idle period if no job has arrived yet
        if current_time < arrival:
            timeline.append({
                "job_id": None,
                "job_name": "Idle",
                "start": current_time,
                "end": arrival,
                "duration": arrival - current_time,
                "type": "idle"
            })
            current_time = arrival
            
        start_time = current_time
        completion_time = start_time + burst
        current_time = completion_time
        
        turnaround_time = completion_time - arrival
        waiting_time = turnaround_time - burst
        tardiness = max(0, completion_time - job.get("deadline", completion_time))
        met_deadline = completion_time <= job.get("deadline", float("inf"))
        
        timeline.append({
            "job_id": job["id"],
            "job_name": job["name"],
            "start": start_time,
            "end": completion_time,
            "duration": burst,
            "type": "job",
            "priority": job.get("priority", 1),
            "profit": job.get("profit", 0)
        })
        
        job_results.append({
            "id": job["id"],
            "name": job["name"],
            "arrival_time": arrival,
            "burst_time": burst,
            "priority": job.get("priority", 1),
            "deadline": job.get("deadline", 0),
            "profit": job.get("profit", 0),
            "start_time": start_time,
            "completion_time": completion_time,
            "turnaround_time": turnaround_time,
            "waiting_time": waiting_time,
            "tardiness": tardiness,
            "met_deadline": met_deadline,
            "status": "Completed"
        })
        
    return {"timeline": timeline, "job_results": job_results}


def sjf_schedule(jobs: List[Dict[str, Any]], preemptive: bool = False) -> Dict[str, Any]:
    """
    Shortest Job First (SJF) or Shortest Remaining Time First (SRTF).
    """
    if not jobs:
        return {"timeline": [], "job_results": [], "metrics": {}}

    if not preemptive:
        # Non-preemptive SJF
        remaining_jobs = [dict(j) for j in jobs]
        current_time = 0
        completed = []
        timeline = []
        
        while remaining_jobs:
            # Jobs that have arrived by current_time
            available = [j for j in remaining_jobs if j["arrival_time"] <= current_time]
            
            if not available:
                # Fast forward to next arriving job
                next_arrival = min(j["arrival_time"] for j in remaining_jobs)
                timeline.append({
                    "job_id": None,
                    "job_name": "Idle",
                    "start": current_time,
                    "end": next_arrival,
                    "duration": next_arrival - current_time,
                    "type": "idle"
                })
                current_time = next_arrival
                continue
                
            # Pick job with shortest burst time (tie-break on arrival time, then id)
            selected = min(available, key=lambda j: (j["burst_time"], j["arrival_time"], j["id"]))
            remaining_jobs.remove(selected)
            
            start_time = current_time
            completion_time = start_time + selected["burst_time"]
            current_time = completion_time
            
            turnaround_time = completion_time - selected["arrival_time"]
            waiting_time = turnaround_time - selected["burst_time"]
            tardiness = max(0, completion_time - selected.get("deadline", completion_time))
            met_deadline = completion_time <= selected.get("deadline", float("inf"))
            
            timeline.append({
                "job_id": selected["id"],
                "job_name": selected["name"],
                "start": start_time,
                "end": completion_time,
                "duration": selected["burst_time"],
                "type": "job",
                "priority": selected.get("priority", 1),
                "profit": selected.get("profit", 0)
            })
            
            completed.append({
                "id": selected["id"],
                "name": selected["name"],
                "arrival_time": selected["arrival_time"],
                "burst_time": selected["burst_time"],
                "priority": selected.get("priority", 1),
                "deadline": selected.get("deadline", 0),
                "profit": selected.get("profit", 0),
                "start_time": start_time,
                "completion_time": completion_time,
                "turnaround_time": turnaround_time,
                "waiting_time": waiting_time,
                "tardiness": tardiness,
                "met_deadline": met_deadline,
                "status": "Completed"
            })
            
        return {"timeline": timeline, "job_results": completed}
    else:
        # Preemptive SJF (SRTF) - Discrete event / unit time simulation
        return _simulate_preemptive(jobs, key_func=lambda j: (j["remaining_time"], j["arrival_time"], j["id"]))


def priority_schedule(jobs: List[Dict[str, Any]], preemptive: bool = False) -> Dict[str, Any]:
    """
    Priority Scheduling (Lower numeric value = higher priority).
    """
    if not jobs:
        return {"timeline": [], "job_results": [], "metrics": {}}

    if not preemptive:
        remaining_jobs = [dict(j) for j in jobs]
        current_time = 0
        completed = []
        timeline = []
        
        while remaining_jobs:
            available = [j for j in remaining_jobs if j["arrival_time"] <= current_time]
            
            if not available:
                next_arrival = min(j["arrival_time"] for j in remaining_jobs)
                timeline.append({
                    "job_id": None,
                    "job_name": "Idle",
                    "start": current_time,
                    "end": next_arrival,
                    "duration": next_arrival - current_time,
                    "type": "idle"
                })
                current_time = next_arrival
                continue
                
            # Pick job with lowest priority value (highest priority)
            selected = min(available, key=lambda j: (j.get("priority", 999), j["arrival_time"], j["id"]))
            remaining_jobs.remove(selected)
            
            start_time = current_time
            completion_time = start_time + selected["burst_time"]
            current_time = completion_time
            
            turnaround_time = completion_time - selected["arrival_time"]
            waiting_time = turnaround_time - selected["burst_time"]
            tardiness = max(0, completion_time - selected.get("deadline", completion_time))
            met_deadline = completion_time <= selected.get("deadline", float("inf"))
            
            timeline.append({
                "job_id": selected["id"],
                "job_name": selected["name"],
                "start": start_time,
                "end": completion_time,
                "duration": selected["burst_time"],
                "type": "job",
                "priority": selected.get("priority", 1),
                "profit": selected.get("profit", 0)
            })
            
            completed.append({
                "id": selected["id"],
                "name": selected["name"],
                "arrival_time": selected["arrival_time"],
                "burst_time": selected["burst_time"],
                "priority": selected.get("priority", 1),
                "deadline": selected.get("deadline", 0),
                "profit": selected.get("profit", 0),
                "start_time": start_time,
                "completion_time": completion_time,
                "turnaround_time": turnaround_time,
                "waiting_time": waiting_time,
                "tardiness": tardiness,
                "met_deadline": met_deadline,
                "status": "Completed"
            })
            
        return {"timeline": timeline, "job_results": completed}
    else:
        # Preemptive Priority
        return _simulate_preemptive(jobs, key_func=lambda j: (j.get("priority", 999), j["arrival_time"], j["id"]))


def edf_schedule(jobs: List[Dict[str, Any]], preemptive: bool = True) -> Dict[str, Any]:
    """
    Earliest Deadline First (EDF) Scheduling.
    Job with closest deadline is scheduled first.
    """
    if not jobs:
        return {"timeline": [], "job_results": [], "metrics": {}}

    if not preemptive:
        remaining_jobs = [dict(j) for j in jobs]
        current_time = 0
        completed = []
        timeline = []
        
        while remaining_jobs:
            available = [j for j in remaining_jobs if j["arrival_time"] <= current_time]
            if not available:
                next_arrival = min(j["arrival_time"] for j in remaining_jobs)
                timeline.append({
                    "job_id": None,
                    "job_name": "Idle",
                    "start": current_time,
                    "end": next_arrival,
                    "duration": next_arrival - current_time,
                    "type": "idle"
                })
                current_time = next_arrival
                continue
                
            selected = min(available, key=lambda j: (j.get("deadline", float("inf")), j["arrival_time"], j["id"]))
            remaining_jobs.remove(selected)
            
            start_time = current_time
            completion_time = start_time + selected["burst_time"]
            current_time = completion_time
            
            turnaround_time = completion_time - selected["arrival_time"]
            waiting_time = turnaround_time - selected["burst_time"]
            tardiness = max(0, completion_time - selected.get("deadline", completion_time))
            met_deadline = completion_time <= selected.get("deadline", float("inf"))
            
            timeline.append({
                "job_id": selected["id"],
                "job_name": selected["name"],
                "start": start_time,
                "end": completion_time,
                "duration": selected["burst_time"],
                "type": "job",
                "priority": selected.get("priority", 1),
                "profit": selected.get("profit", 0)
            })
            
            completed.append({
                "id": selected["id"],
                "name": selected["name"],
                "arrival_time": selected["arrival_time"],
                "burst_time": selected["burst_time"],
                "priority": selected.get("priority", 1),
                "deadline": selected.get("deadline", 0),
                "profit": selected.get("profit", 0),
                "start_time": start_time,
                "completion_time": completion_time,
                "turnaround_time": turnaround_time,
                "waiting_time": waiting_time,
                "tardiness": tardiness,
                "met_deadline": met_deadline,
                "status": "Completed"
            })
            
        return {"timeline": timeline, "job_results": completed}
    else:
        return _simulate_preemptive(jobs, key_func=lambda j: (j.get("deadline", float("inf")), j["arrival_time"], j["id"]))


def job_sequencing_with_deadlines(jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Classic Greedy Job Sequencing with Deadlines & Profits.
    Each job takes 1 unit of time (or burst_time unit slots), has a deadline and profit.
    Jobs are sorted by profit in descending order, then scheduled in the latest free slot <= deadline.
    """
    if not jobs:
        return {"timeline": [], "job_results": [], "metrics": {}}

    sorted_jobs = sorted(jobs, key=lambda j: j.get("profit", 0), reverse=True)
    max_deadline = max(j.get("deadline", 1) for j in sorted_jobs)
    
    # Slot 1 to max_deadline
    slots = [None] * (max_deadline + 1)
    scheduled_job_map = {}
    
    for job in sorted_jobs:
        deadline = min(job.get("deadline", 1), max_deadline)
        # Find latest available slot <= deadline
        for t in range(deadline, 0, -1):
            if slots[t] is None:
                slots[t] = job
                scheduled_job_map[job["id"]] = t
                break
                
    timeline = []
    job_results = []
    
    current_time = 0
    for t in range(1, max_deadline + 1):
        job = slots[t]
        slot_start = t - 1
        slot_end = t
        if job:
            timeline.append({
                "job_id": job["id"],
                "job_name": job["name"],
                "start": slot_start,
                "end": slot_end,
                "duration": 1,
                "type": "job",
                "priority": job.get("priority", 1),
                "profit": job.get("profit", 0)
            })
        else:
            timeline.append({
                "job_id": None,
                "job_name": "Idle",
                "start": slot_start,
                "end": slot_end,
                "duration": 1,
                "type": "idle"
            })
            
    # Coalesce consecutive idle or identical job slots
    coalesced_timeline = _coalesce_timeline(timeline)
    
    for job in jobs:
        is_scheduled = job["id"] in scheduled_job_map
        if is_scheduled:
            slot_t = scheduled_job_map[job["id"]]
            completion_time = slot_t
            start_time = slot_t - 1
            tat = completion_time - job.get("arrival_time", 0)
            wt = tat - 1
            job_results.append({
                "id": job["id"],
                "name": job["name"],
                "arrival_time": job.get("arrival_time", 0),
                "burst_time": 1,
                "priority": job.get("priority", 1),
                "deadline": job.get("deadline", 0),
                "profit": job.get("profit", 0),
                "start_time": start_time,
                "completion_time": completion_time,
                "turnaround_time": tat,
                "waiting_time": max(0, wt),
                "tardiness": 0,
                "met_deadline": True,
                "status": "Scheduled"
            })
        else:
            job_results.append({
                "id": job["id"],
                "name": job["name"],
                "arrival_time": job.get("arrival_time", 0),
                "burst_time": job.get("burst_time", 1),
                "priority": job.get("priority", 1),
                "deadline": job.get("deadline", 0),
                "profit": job.get("profit", 0),
                "start_time": None,
                "completion_time": None,
                "turnaround_time": 0,
                "waiting_time": 0,
                "tardiness": 0,
                "met_deadline": False,
                "status": "Rejected (Exceeded Deadline)"
            })
            
    return {"timeline": coalesced_timeline, "job_results": job_results}


def _simulate_preemptive(jobs: List[Dict[str, Any]], key_func) -> Dict[str, Any]:
    """
    Generic preemptive scheduler engine tracking unit or event steps.
    """
    sim_jobs = {}
    for j in jobs:
        sim_jobs[j["id"]] = {
            **j,
            "remaining_time": j["burst_time"],
            "first_start_time": None,
            "completion_time": None
        }
        
    all_arrivals = sorted(set(j["arrival_time"] for j in jobs))
    total_burst = sum(j["burst_time"] for j in jobs)
    
    current_time = 0
    raw_timeline = []
    completed_ids = set()
    total_jobs = len(jobs)
    
    # Run discrete unit simulation
    while len(completed_ids) < total_jobs:
        # Check which jobs have arrived and are incomplete
        ready = [j for j in sim_jobs.values() if j["arrival_time"] <= current_time and j["id"] not in completed_ids]
        
        if not ready:
            # Advance to next arrival
            unstarted = [j for j in sim_jobs.values() if j["id"] not in completed_ids]
            if not unstarted:
                break
            next_arrival = min(j["arrival_time"] for j in unstarted)
            raw_timeline.append({
                "job_id": None,
                "job_name": "Idle",
                "start": current_time,
                "end": next_arrival,
                "duration": next_arrival - current_time,
                "type": "idle"
            })
            current_time = next_arrival
            continue
            
        # Select best candidate
        chosen = min(ready, key=key_func)
        job_id = chosen["id"]
        
        if chosen["first_start_time"] is None:
            chosen["first_start_time"] = current_time
            
        # Determine duration to next critical event:
        # 1. Job completes
        # 2. Another job arrives that could preempt
        future_arrivals = [t for t in all_arrivals if t > current_time]
        next_event_time = current_time + chosen["remaining_time"]
        
        if future_arrivals:
            earliest_future_arrival = future_arrivals[0]
            if earliest_future_arrival < next_event_time:
                run_duration = earliest_future_arrival - current_time
            else:
                run_duration = chosen["remaining_time"]
        else:
            run_duration = chosen["remaining_time"]
            
        run_end = current_time + run_duration
        chosen["remaining_time"] -= run_duration
        
        raw_timeline.append({
            "job_id": chosen["id"],
            "job_name": chosen["name"],
            "start": current_time,
            "end": run_end,
            "duration": run_duration,
            "type": "job",
            "priority": chosen.get("priority", 1),
            "profit": chosen.get("profit", 0)
        })
        
        current_time = run_end
        
        if chosen["remaining_time"] == 0:
            chosen["completion_time"] = current_time
            completed_ids.add(job_id)
            
    coalesced_timeline = _coalesce_timeline(raw_timeline)
    
    job_results = []
    for j in jobs:
        info = sim_jobs[j["id"]]
        ct = info["completion_time"]
        arr = j["arrival_time"]
        burst = j["burst_time"]
        tat = ct - arr if ct is not None else 0
        wt = tat - burst if ct is not None else 0
        deadline = j.get("deadline", ct)
        tardiness = max(0, ct - deadline) if ct is not None else 0
        met = ct <= deadline if ct is not None else False
        
        job_results.append({
            "id": j["id"],
            "name": j["name"],
            "arrival_time": arr,
            "burst_time": burst,
            "priority": j.get("priority", 1),
            "deadline": j.get("deadline", 0),
            "profit": j.get("profit", 0),
            "start_time": info["first_start_time"],
            "completion_time": ct,
            "turnaround_time": tat,
            "waiting_time": wt,
            "tardiness": tardiness,
            "met_deadline": met,
            "status": "Completed"
        })
        
    return {"timeline": coalesced_timeline, "job_results": job_results}


def _coalesce_timeline(timeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Merges adjacent timeline segments of the same job or idle state."""
    if not timeline:
        return []
    coalesced = []
    current = dict(timeline[0])
    
    for item in timeline[1:]:
        if item["job_id"] == current["job_id"] and item["start"] == current["end"]:
            current["end"] = item["end"]
            current["duration"] += item["duration"]
        else:
            coalesced.append(current)
            current = dict(item)
    coalesced.append(current)
    return coalesced


# =========================================================================
# PHASE 4: DAA GREEDY JOB SCHEDULING ALGORITHM WITH RESOURCE ALLOCATION
# =========================================================================

import time
from typing import Tuple

def _normalize_priority(p: Any) -> Tuple[int, str]:
    """
    Normalizes priority into (numeric_score, label).
    Higher numeric_score means higher priority.
    Ordering: High (3) > Medium (2) > Low (1).
    """
    if isinstance(p, str):
        cleaned = p.strip().capitalize()
        if cleaned in ["High", "1", "Urgent", "Critical"]:
            return (3, "High")
        elif cleaned in ["Medium", "2", "Normal"]:
            return (2, "Medium")
        elif cleaned in ["Low", "3", "4", "5"]:
            return (1, "Low")
        return (2, cleaned)
    elif isinstance(p, (int, float)):
        if p <= 1:
            return (3, "High")
        elif p == 2:
            return (2, "Medium")
        else:
            return (1, "Low")
    return (2, "Medium")


def is_resource_compatible(resource: Dict[str, Any], required: str) -> bool:
    """
    Validates whether a resource satisfies a job's resource constraint.
    Never assigns a Machine-required job to an Employee or vice-versa.
    """
    if not required or not str(required).strip():
        return True
    req = str(required).strip().lower()
    if req in ["any", "all", "any compatible", "any available", "none", "compat"]:
        return True

    r_type = str(resource.get("resource_type", "")).strip().lower()
    r_id = str(resource.get("resource_id", "")).strip().lower()
    r_name = str(resource.get("resource_name", "")).strip().lower()

    if req == r_type or req == r_id:
        return True

    standard_types = {"employee", "machine", "computer", "vehicle", "server", "other"}
    if req in standard_types:
        return r_type == req

    return req == r_name or req in r_name


def greedy_job_scheduling(jobs: List[Dict[str, Any]], resources: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Resource-Aware Greedy Job Scheduling Algorithm.
    
    Greedy Strategy:
    1. Primary Selection Criterion: Higher profit first (descending: -profit).
    2. Tie-Breaking Rule 1: Earlier deadline first (ascending: deadline).
    3. Tie-Breaking Rule 2: Higher priority next (descending: -priority_score: High=3 > Medium=2 > Low=1).
    4. Tie-Breaking Rule 3: Shorter processing time / burst time next (ascending: processing_time).
    5. Tie-Breaking Rule 4: Job ID (ascending: id).
    
    Resource Allocation Greedy Rule:
    - Inspect only available and compatible resources (never Machine to Employee or vice versa).
    - Valid start time: start_time = max(resource.current_finish_time, arrival_time).
    - Finish time: finish_time = start_time + processing_time.
    - Feasibility conditions:
      1) finish_time <= deadline
      2) finish_time <= resource.available_hours
      3) resource.used_hours + processing_time <= resource.available_hours
    - Non-overlapping execution on exclusive resources guaranteed by advancing resource.current_finish_time.
    - If multiple resources qualify: Pick the one with the largest remaining available hours after placement
      (tie-break: earlier start_time, then alphabetical resource_id).
    
    Truthful Rejection Categorization:
    - DEADLINE_EXCEEDED: arrival_time + processing_time > deadline
    - NO_COMPATIBLE_RESOURCE: no available resource matches required type
    - RESOURCE_CAPACITY_EXCEEDED: compatible resources exist but individual capacity < processing_time
    - NO_FEASIBLE_SLOT: cannot be scheduled without violating deadline or remaining capacity
    
    Complexity Analysis:
    - Sorting N candidate jobs: O(N log N)
    - Resource feasibility check for M resources per job: O(N * M)
    - Total Time Complexity: O(N log N + N * M)
    - Auxiliary Space Complexity: O(N + M)
    """
    start_time_perf = time.perf_counter()

    # Pre-process resources: only Available resources participate in scheduling
    res_pool = {}
    for r in resources:
        if r.get("status") == "Available":
            res_id = str(r.get("resource_id") or r.get("id", "RES-000")).strip()
            res_name = str(r.get("resource_name") or res_id).strip()
            res_type = str(r.get("resource_type") or "Other").strip()
            try:
                total_h = float(r.get("available_hours", 8.0))
            except (ValueError, TypeError):
                total_h = 8.0
            total_h = max(0.0, total_h)

            res_pool[res_id] = {
                "id": r.get("id"),
                "resource_id": res_id,
                "resource_name": res_name,
                "resource_type": res_type,
                "total_hours": total_h,
                "available_hours": total_h,
                "used_hours": 0.0,
                "remaining_hours": total_h,
                "current_timeline_end": 0.0,
                "intervals": [],
                "scheduled_jobs": []
            }

    total_res_capacity = sum(r["total_hours"] for r in res_pool.values())

    if not jobs:
        execution_time_sec = round(time.perf_counter() - start_time_perf, 6)
        return {
            "scheduled_jobs": [],
            "missed_jobs": [],
            "all_processed_jobs": [],
            "schedules": [],
            "resource_states": res_pool,
            "metrics": {
                "total_jobs": 0,
                "scheduled_count": 0,
                "missed_count": 0,
                "total_profit": 0.0,
                "total_processing_time": 0.0,
                "resource_utilization": 0.0,
                "deadline_success_rate": 0.0,
                "on_time_rate": 0.0,
                "total_resource_hours": round(total_res_capacity, 2),
                "used_resource_hours": 0.0,
                "makespan": 0.0
            },
            "execution_time": execution_time_sec,
            "num_jobs": 0,
            "num_resources": len(res_pool),
            "step_by_step_log": [],
            "algorithm": "Greedy",
            "message": "No jobs available for scheduling."
        }

    scheduled_jobs = []
    missed_jobs = []
    schedules_to_save = []
    decision_logs = []

    # Pre-process candidate jobs
    prepared_jobs = []
    for j in jobs:
        pri_score, pri_label = _normalize_priority(j.get("priority", "Medium"))
        try:
            processing_time = float(j.get("burst_time", j.get("processing_time", 1)))
        except (ValueError, TypeError):
            processing_time = 0.0

        if processing_time <= 0:
            job_id_val = j.get("id", 1)
            missed_jobs.append({
                **j,
                "id": job_id_val,
                "job_id": job_id_val,
                "name": str(j.get("name", f"Job {job_id_val}")),
                "status": "Missed",
                "assigned_resource_id": "None",
                "assigned_resource_name": "None",
                "start_time": None,
                "end_time": None,
                "missed_reason": "INVALID_INPUT",
                "missed_explanation": f"Job processing time must be strictly positive (> 0), got {processing_time}.",
                "full_missed_reason": f"INVALID_INPUT: Job processing time must be strictly positive (> 0), got {processing_time}."
            })
            continue

        try:
            profit = float(j.get("profit", 0))
        except (ValueError, TypeError):
            profit = 0.0
        profit = max(0.0, profit)

        try:
            deadline = float(j.get("deadline", 999))
        except (ValueError, TypeError):
            deadline = 999.0

        try:
            arrival_time = float(j.get("arrival_time", 0))
        except (ValueError, TypeError):
            arrival_time = 0.0
        arrival_time = max(0.0, arrival_time)

        req_res = str(j.get("required_resource") or "").strip()
        job_id_val = j.get("id", 1)
        job_code = f"J{job_id_val:03d}" if isinstance(job_id_val, int) else str(job_id_val)

        prepared_jobs.append({
            "original": j,
            "id": job_id_val,
            "job_id": job_id_val,
            "job_code": job_code,
            "name": str(j.get("name", f"Job {job_id_val}")),
            "processing_time": processing_time,
            "burst_time": processing_time,
            "profit": profit,
            "deadline": deadline,
            "arrival_time": arrival_time,
            "priority_score": pri_score,
            "priority": pri_label,
            "priority_label": pri_label,
            "required_resource": req_res,
            "color": j.get("color", "#6366F1")
        })

    # GREEDY SORTING:
    # 1. Higher profit first (descending: -profit)
    # 2. Earlier deadline first (ascending: deadline)
    # 3. Higher priority next (descending: -priority_score)
    # 4. Shorter processing time next (ascending: processing_time)
    # 5. Job ID (ascending: id)
    sorted_candidates = sorted(
        prepared_jobs,
        key=lambda x: (
            -x["profit"],
            x["deadline"],
            -x["priority_score"],
            x["processing_time"],
            x["id"] if isinstance(x["id"], int) else 0
        )
    )

    # Sequential Greedy Selection & Allocation
    for step_idx, job in enumerate(sorted_candidates, start=1):
        p_time = job["processing_time"]
        dl = job["deadline"]
        arr = job["arrival_time"]
        req = job["required_resource"]

        # 1. Inherent deadline impossibility check
        if arr + p_time > dl:
            fail_reason = "DEADLINE_EXCEEDED"
            fail_desc = f"Processing time ({p_time:g} hrs) from arrival (t={arr:g}) exceeds deadline (t={dl:g})."
            missed_jobs.append({
                **job,
                "status": "Missed",
                "assigned_resource_id": "None",
                "assigned_resource_name": "None",
                "start_time": None,
                "end_time": None,
                "missed_reason": fail_reason,
                "missed_explanation": fail_desc,
                "full_missed_reason": f"{fail_reason}: {fail_desc}"
            })
            decision_logs.append({
                "step": step_idx,
                "job_name": job["name"],
                "decision": "Missed",
                "reason": fail_desc
            })
            continue

        # 2. Inspect compatible available resources
        matching_resources = [
            r for r in res_pool.values()
            if is_resource_compatible(r, req)
        ]

        if not matching_resources:
            fail_reason = "NO_COMPATIBLE_RESOURCE"
            fail_desc = f"No available resource matches required type '{req or 'Any'}'."
            missed_jobs.append({
                **job,
                "status": "Missed",
                "assigned_resource_id": "None",
                "assigned_resource_name": "None",
                "start_time": None,
                "end_time": None,
                "missed_reason": fail_reason,
                "missed_explanation": fail_desc,
                "full_missed_reason": f"{fail_reason}: {fail_desc}"
            })
            decision_logs.append({
                "step": step_idx,
                "job_name": job["name"],
                "decision": "Missed",
                "reason": fail_desc
            })
            continue

        # 3. Check individual total capacity limit
        if all(r["total_hours"] < p_time for r in matching_resources):
            fail_reason = "RESOURCE_CAPACITY_EXCEEDED"
            fail_desc = f"Job duration ({p_time:g} hrs) exceeds total capacity of compatible resources."
            missed_jobs.append({
                **job,
                "status": "Missed",
                "assigned_resource_id": "None",
                "assigned_resource_name": "None",
                "start_time": None,
                "end_time": None,
                "missed_reason": fail_reason,
                "missed_explanation": fail_desc,
                "full_missed_reason": f"{fail_reason}: {fail_desc}"
            })
            decision_logs.append({
                "step": step_idx,
                "job_name": job["name"],
                "decision": "Missed",
                "reason": fail_desc
            })
            continue

        # 4. Find feasible resources and earliest idle gaps that can place the job
        feasible_candidates = []
        for r in matching_resources:
            if (r["used_hours"] + p_time) > r["total_hours"]:
                continue

            # Compute all available gaps on this resource
            intervals = r.get("intervals", [])
            total_h = r["total_hours"]
            gaps = []
            if not intervals:
                gaps.append((0.0, total_h))
            else:
                if intervals[0][0] > 0.0:
                    gaps.append((0.0, intervals[0][0]))
                for i in range(len(intervals) - 1):
                    if intervals[i + 1][0] > intervals[i][1]:
                        gaps.append((intervals[i][1], intervals[i + 1][0]))
                if total_h > intervals[-1][1]:
                    gaps.append((intervals[-1][1], total_h))

            # Find the earliest feasible slot in these gaps
            for gap_start, gap_end in gaps:
                cand_start = max(gap_start, arr)
                cand_end = cand_start + p_time
                if cand_end <= gap_end and cand_end <= dl and cand_end <= total_h:
                    feasible_candidates.append({
                        "resource": r,
                        "start_time": cand_start,
                        "end_time": cand_end,
                        "remaining_after": r["remaining_hours"] - p_time
                    })
                    break  # Take earliest feasible gap on this resource

        if not feasible_candidates:
            fail_reason = "NO_FEASIBLE_SLOT"
            fail_desc = f"Cannot be scheduled on compatible resources without exceeding deadline (t={dl:g}) or capacity."
            missed_jobs.append({
                **job,
                "status": "Missed",
                "assigned_resource_id": "None",
                "assigned_resource_name": "None",
                "start_time": None,
                "end_time": None,
                "missed_reason": fail_reason,
                "missed_explanation": fail_desc,
                "full_missed_reason": f"{fail_reason}: {fail_desc}"
            })
            decision_logs.append({
                "step": step_idx,
                "job_name": job["name"],
                "decision": "Missed",
                "reason": fail_desc
            })
            continue

        # 5. Greedy Selection: Pick resource with earliest start time (earliest finish / earliest gap)
        # Tie-break 1: Largest remaining capacity after placement
        # Tie-break 2: Alphabetical resource_id
        selected_choice = min(
            feasible_candidates,
            key=lambda c: (
                c["start_time"],
                -c["remaining_after"],
                c["resource"]["resource_id"]
            )
        )

        selected_res = selected_choice["resource"]
        start_t = selected_choice["start_time"]
        end_t = selected_choice["end_time"]

        # Update resource timeline state and sorted intervals
        selected_res["intervals"].append((start_t, end_t))
        selected_res["intervals"].sort(key=lambda iv: iv[0])
        selected_res["current_timeline_end"] = max(iv[1] for iv in selected_res["intervals"])
        selected_res["used_hours"] += p_time
        selected_res["remaining_hours"] -= p_time

        scheduled_entry = {
            **job,
            "status": "Scheduled",
            "assigned_resource_id": selected_res["resource_id"],
            "assigned_resource_name": selected_res["resource_name"],
            "start_time": start_t,
            "end_time": end_t
        }
        scheduled_jobs.append(scheduled_entry)
        selected_res["scheduled_jobs"].append(scheduled_entry)

        schedules_to_save.append({
            "id": job["id"],
            "job_id": job["id"],
            "name": job["name"],
            "job_name": job["name"],
            "processing_time": p_time,
            "burst_time": p_time,
            "deadline": dl,
            "start_time": start_t,
            "end_time": end_t,
            "finish_time": end_t,
            "assigned_resource_id": selected_res["resource_id"],
            "resource_id": selected_res["resource_id"],
            "resource_name": selected_res["resource_name"],
            "resource_type": selected_res["resource_type"],
            "profit": job["profit"],
            "priority": job["priority_label"],
            "status": "Scheduled",
            "algorithm": "Greedy"
        })

        decision_logs.append({
            "step": step_idx,
            "job_name": job["name"],
            "decision": "Scheduled",
            "reason": f"Allocated to {selected_res['resource_id']} ({selected_res['resource_name']}) for [t={start_t:g} -> t={end_t:g}]."
        })

    execution_time_sec = round(time.perf_counter() - start_time_perf, 6)

    # Calculate real, validated metrics
    total_candidate_jobs = len(scheduled_jobs) + len(missed_jobs)
    total_profit = sum(j["profit"] for j in scheduled_jobs)
    total_proc_time = sum(j["processing_time"] for j in scheduled_jobs)
    total_res_used = sum(r["used_hours"] for r in res_pool.values())
    makespan = max((s["end_time"] for s in schedules_to_save), default=0.0)

    utilization_pct = round((total_res_used / total_res_capacity * 100.0), 2) if total_res_capacity > 0 else 0.0
    
    # On-time completion rate: scheduled jobs completing by deadline / scheduled jobs * 100
    on_time_count = sum(1 for j in scheduled_jobs if j["end_time"] <= j["deadline"])
    on_time_rate = round((on_time_count / len(scheduled_jobs) * 100.0), 2) if scheduled_jobs else 0.0

    return {
        "scheduled_jobs": scheduled_jobs,
        "missed_jobs": missed_jobs,
        "all_processed_jobs": scheduled_jobs + missed_jobs,
        "schedules": schedules_to_save,
        "resource_states": res_pool,
        "metrics": {
            "total_jobs": total_candidate_jobs,
            "scheduled_count": len(scheduled_jobs),
            "missed_count": len(missed_jobs),
            "total_profit": total_profit,
            "total_processing_time": total_proc_time,
            "resource_utilization": utilization_pct,
            "deadline_success_rate": on_time_rate,
            "on_time_rate": on_time_rate,
            "on_time_count": on_time_count,
            "total_resource_hours": round(total_res_capacity, 2),
            "used_resource_hours": round(total_res_used, 2),
            "makespan": makespan
        },
        "execution_time": execution_time_sec,
        "num_jobs": len(prepared_jobs),
        "num_resources": len(resources),
        "step_by_step_log": decision_logs,
        "algorithm": "Greedy",
        "message": f"Greedy Algorithm executed successfully: {len(scheduled_jobs)} scheduled, {len(missed_jobs)} missed (Total Profit: ${total_profit})."
    }
