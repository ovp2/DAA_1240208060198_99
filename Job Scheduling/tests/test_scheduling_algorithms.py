"""
Automated Test Suite for Job Scheduling Algorithms (Greedy & Dynamic Programming)
Covers all 10 specific DAA requirements:
1. A job finishing exactly at its deadline.
2. A job missing its deadline.
3. Two jobs competing for one resource.
4. Jobs running concurrently on different resources.
5. An incompatible resource.
6. A job that can be scheduled only in an earlier slot.
7. Empty input and zero capacity.
8. The eight-job dataset currently used by the application.
9. Agreement between the selected-job list, profit, processing time, and displayed DP result.
10. DP optimality against exhaustive enumeration for small instances of the same problem model.
"""

import unittest
import sys
import os

REPO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_DIR not in sys.path:
    sys.path.insert(0, REPO_DIR)

from algorithms.greedy import greedy_job_scheduling
from algorithms.dynamic_programming import dynamic_programming_job_scheduling, validate_schedule


class TestJobSchedulingAlgorithms(unittest.TestCase):

    def setUp(self):
        self.standard_employee = {
            "id": 1,
            "resource_id": "R001",
            "resource_name": "Developer Lead",
            "resource_type": "Employee",
            "available_hours": 8.0,
            "status": "Available"
        }
        self.standard_machine = {
            "id": 2,
            "resource_id": "R002",
            "resource_name": "Database Server",
            "resource_type": "Machine",
            "available_hours": 12.0,
            "status": "Available"
        }
        self.standard_computer = {
            "id": 3,
            "resource_id": "R003",
            "resource_name": "Compute Cluster",
            "resource_type": "Computer",
            "available_hours": 16.0,
            "status": "Available"
        }
        self.second_employee = {
            "id": 4,
            "resource_id": "R004",
            "resource_name": "QA Engineer",
            "resource_type": "Employee",
            "available_hours": 8.0,
            "status": "Available"
        }

    # --------------------------------------------------------------------------
    # 1. A job finishing exactly at its deadline
    # --------------------------------------------------------------------------
    def test_01_job_finishing_exactly_at_deadline(self):
        """1. A job whose finish_time == deadline must be accepted if all other constraints pass."""
        jobs = [{
            "id": 1,
            "name": "Exact-Deadline-Task",
            "processing_time": 4.0,
            "burst_time": 4.0,
            "deadline": 4.0,
            "profit": 100,
            "priority": "High",
            "required_resource": "Employee"
        }]
        resources = [self.standard_employee]

        for alg_name, scheduler in [("Greedy", greedy_job_scheduling), ("DP", dynamic_programming_job_scheduling)]:
            res = scheduler(jobs, resources)
            self.assertEqual(len(res["schedules"]), 1, f"{alg_name} should accept job finishing exactly at deadline")
            self.assertEqual(len(res["missed_jobs"]), 0)
            
            s = res["schedules"][0]
            self.assertEqual(s["start_time"], 0.0)
            self.assertEqual(s["end_time"], 4.0)
            self.assertEqual(s["end_time"], s["deadline"])
            
            val = validate_schedule(res["schedules"], resources, jobs)
            self.assertTrue(val["valid"], f"{alg_name} validator failed: {val.get('error')}")

    # --------------------------------------------------------------------------
    # 2. A job missing its deadline
    # --------------------------------------------------------------------------
    def test_02_job_missing_deadline(self):
        """2. A job that misses its deadline (p=5, dl=4) must be rejected with DEADLINE_EXCEEDED."""
        jobs = [{
            "id": 2,
            "name": "Overdue-Task",
            "processing_time": 5.0,
            "burst_time": 5.0,
            "deadline": 4.0,
            "profit": 100,
            "priority": "High",
            "required_resource": "Employee"
        }]
        resources = [self.standard_employee]

        for alg_name, scheduler in [("Greedy", greedy_job_scheduling), ("DP", dynamic_programming_job_scheduling)]:
            res = scheduler(jobs, resources)
            self.assertEqual(len(res["schedules"]), 0, f"{alg_name} must reject job missing deadline")
            self.assertEqual(len(res["missed_jobs"]), 1)
            self.assertEqual(res["missed_jobs"][0]["missed_reason"], "DEADLINE_EXCEEDED")

    # --------------------------------------------------------------------------
    # 3. Two jobs competing for one resource
    # --------------------------------------------------------------------------
    def test_03_two_jobs_competing_one_resource(self):
        """3. Two jobs on the same exclusive resource must execute sequentially without overlapping."""
        jobs = [
            {"id": 31, "name": "Task-A", "processing_time": 3.0, "burst_time": 3.0, "deadline": 8.0, "profit": 100, "priority": "High", "required_resource": "Employee"},
            {"id": 32, "name": "Task-B", "processing_time": 3.0, "burst_time": 3.0, "deadline": 8.0, "profit": 80, "priority": "Medium", "required_resource": "Employee"}
        ]
        resources = [self.standard_employee]

        for alg_name, scheduler in [("Greedy", greedy_job_scheduling), ("DP", dynamic_programming_job_scheduling)]:
            res = scheduler(jobs, resources)
            self.assertEqual(len(res["schedules"]), 2, f"{alg_name} should sequence both jobs")
            
            ordered = sorted(res["schedules"], key=lambda s: s["start_time"])
            self.assertGreaterEqual(ordered[1]["start_time"], ordered[0]["end_time"], "Overlapping execution detected!")
            
            val = validate_schedule(res["schedules"], resources, jobs)
            self.assertTrue(val["valid"], f"{alg_name} validator failed: {val.get('error')}")

    # --------------------------------------------------------------------------
    # 4. Jobs running concurrently on different resources
    # --------------------------------------------------------------------------
    def test_04_jobs_running_concurrently_different_resources(self):
        """4. Jobs requiring different compatible resources should execute in parallel (both start at t=0)."""
        jobs = [
            {"id": 41, "name": "Emp-Job", "processing_time": 4.0, "burst_time": 4.0, "deadline": 6.0, "profit": 100, "priority": "High", "required_resource": "Employee"},
            {"id": 42, "name": "Mach-Job", "processing_time": 4.0, "burst_time": 4.0, "deadline": 6.0, "profit": 120, "priority": "High", "required_resource": "Machine"}
        ]
        resources = [self.standard_employee, self.standard_machine]

        for alg_name, scheduler in [("Greedy", greedy_job_scheduling), ("DP", dynamic_programming_job_scheduling)]:
            res = scheduler(jobs, resources)
            self.assertEqual(len(res["schedules"]), 2)
            
            s_map = {s["id"]: s for s in res["schedules"]}
            self.assertEqual(s_map[41]["start_time"], 0.0)
            self.assertEqual(s_map[42]["start_time"], 0.0)
            self.assertEqual(s_map[41]["assigned_resource_id"], "R001")
            self.assertEqual(s_map[42]["assigned_resource_id"], "R002")
            
            val = validate_schedule(res["schedules"], resources, jobs)
            self.assertTrue(val["valid"], f"{alg_name} validator failed: {val.get('error')}")

    # --------------------------------------------------------------------------
    # 5. An incompatible resource
    # --------------------------------------------------------------------------
    def test_05_incompatible_resource(self):
        """5. A job requiring Machine when only Employee is available must be rejected with NO_COMPATIBLE_RESOURCE."""
        jobs = [{
            "id": 51,
            "name": "Machine-Workload",
            "processing_time": 2.0,
            "burst_time": 2.0,
            "deadline": 8.0,
            "profit": 90,
            "priority": "High",
            "required_resource": "Machine"
        }]
        resources = [self.standard_employee]  # Only Employee available

        for alg_name, scheduler in [("Greedy", greedy_job_scheduling), ("DP", dynamic_programming_job_scheduling)]:
            res = scheduler(jobs, resources)
            self.assertEqual(len(res["schedules"]), 0)
            self.assertEqual(len(res["missed_jobs"]), 1)
            self.assertEqual(res["missed_jobs"][0]["missed_reason"], "NO_COMPATIBLE_RESOURCE")

    # --------------------------------------------------------------------------
    # 6. A job that can be scheduled only in an earlier slot
    # --------------------------------------------------------------------------
    def test_06_job_scheduled_only_in_earlier_slot(self):
        """6. A job with an earlier deadline (dl=3) cannot fit in a later slot (t=3 to 6).
        DP globally optimizes: places Early-Job in [0, 3] and Late-Job in [3, 6].
        Greedy demonstrates heuristic trade-off: picks higher-profit Late-Job first at [0, 3],
        leaving Early-Job with NO_FEASIBLE_SLOT because t=3..6 exceeds deadline 3.
        When profits are equal, Greedy's deadline tie-breaker places Early-Job in [0, 3].
        """
        jobs = [
            {"id": 61, "name": "Early-Job", "processing_time": 3.0, "burst_time": 3.0, "deadline": 3.0, "profit": 80, "priority": "High", "required_resource": "Employee"},
            {"id": 62, "name": "Late-Job", "processing_time": 3.0, "burst_time": 3.0, "deadline": 6.0, "profit": 100, "priority": "High", "required_resource": "Employee"}
        ]
        resources = [self.standard_employee]

        # 1. DP finds global optimum: schedules Early-Job in [0, 3] and Late-Job in [3, 6]
        dp_res = dynamic_programming_job_scheduling(jobs, resources)
        self.assertEqual(len(dp_res["schedules"]), 2)
        s_map = {s["id"]: s for s in dp_res["schedules"]}
        self.assertEqual(s_map[61]["start_time"], 0.0)
        self.assertEqual(s_map[61]["end_time"], 3.0)
        self.assertEqual(s_map[62]["start_time"], 3.0)
        self.assertEqual(s_map[62]["end_time"], 6.0)
        val = validate_schedule(dp_res["schedules"], resources, jobs)
        self.assertTrue(val["valid"], f"DP validator failed: {val.get('error')}")

        # 2. Greedy: picks Late-Job (profit 100 > 80) at [0, 3]. Early-Job misses deadline in [3, 6].
        greedy_res = greedy_job_scheduling(jobs, resources)
        self.assertEqual(len(greedy_res["schedules"]), 1)
        self.assertEqual(greedy_res["schedules"][0]["id"], 62)
        self.assertEqual(len(greedy_res["missed_jobs"]), 1)
        self.assertEqual(greedy_res["missed_jobs"][0]["id"], 61)
        self.assertEqual(greedy_res["missed_jobs"][0]["missed_reason"], "NO_FEASIBLE_SLOT")

        # 3. Equal-profit test: Greedy's earlier-deadline tie-breaker places Early-Job in [0, 3]
        equal_jobs = [
            {"id": 61, "name": "Early-Job", "processing_time": 3.0, "burst_time": 3.0, "deadline": 3.0, "profit": 100, "priority": "High", "required_resource": "Employee"},
            {"id": 62, "name": "Late-Job", "processing_time": 3.0, "burst_time": 3.0, "deadline": 6.0, "profit": 100, "priority": "High", "required_resource": "Employee"}
        ]
        greedy_eq = greedy_job_scheduling(equal_jobs, resources)
        self.assertEqual(len(greedy_eq["schedules"]), 2)
        eq_map = {s["id"]: s for s in greedy_eq["schedules"]}
        self.assertEqual(eq_map[61]["start_time"], 0.0)
        self.assertEqual(eq_map[62]["start_time"], 3.0)

    # --------------------------------------------------------------------------
    # 6. A job cannot be scheduled twice
    # --------------------------------------------------------------------------
    def test_06_job_cannot_be_scheduled_twice(self):
        """6. No job is ever scheduled more than once across any resource."""
        jobs = [
            {"id": 601, "name": "Unique-Job-A", "processing_time": 2.0, "burst_time": 2.0, "deadline": 6.0, "profit": 50, "priority": "High", "required_resource": "Employee"},
            {"id": 602, "name": "Unique-Job-B", "processing_time": 3.0, "burst_time": 3.0, "deadline": 6.0, "profit": 70, "priority": "High", "required_resource": "Employee"}
        ]
        resources = [self.standard_employee, self.second_employee]

        for alg_name, scheduler in [("Greedy", greedy_job_scheduling), ("DP", dynamic_programming_job_scheduling)]:
            res = scheduler(jobs, resources)
            scheduled_ids = [s["id"] for s in res["schedules"]]
            self.assertEqual(len(scheduled_ids), len(set(scheduled_ids)), f"{alg_name} contains duplicate jobs")
            val = validate_schedule(res["schedules"], resources, jobs)
            self.assertTrue(val["valid"], f"{alg_name} validator failed: {val.get('error')}")

    # --------------------------------------------------------------------------
    # 7. An unavailable resource cannot receive a job during unavailable hours
    # --------------------------------------------------------------------------
    def test_07_unavailable_resource_cannot_receive_job(self):
        """7. Resources marked Maintenance/Offline or having 0 capacity are not assigned any jobs."""
        offline_employee = {
            "id": 99,
            "resource_id": "R099",
            "resource_name": "Offline Dev",
            "resource_type": "Employee",
            "available_hours": 8.0,
            "status": "Maintenance"
        }
        job = [{"id": 701, "name": "Task", "processing_time": 2.0, "burst_time": 2.0, "deadline": 4.0, "profit": 50, "priority": "High", "required_resource": "Employee"}]

        for alg_name, scheduler in [("Greedy", greedy_job_scheduling), ("DP", dynamic_programming_job_scheduling)]:
            res = scheduler(job, [offline_employee])
            self.assertEqual(len(res["schedules"]), 0, f"{alg_name} should not schedule on offline resource")
            self.assertEqual(len(res["missed_jobs"]), 1)
            self.assertEqual(res["missed_jobs"][0]["missed_reason"], "NO_COMPATIBLE_RESOURCE")

    # --------------------------------------------------------------------------
    # 8. Skipped jobs do not contribute to total profit
    # --------------------------------------------------------------------------
    def test_08_skipped_jobs_do_not_contribute_to_profit(self):
        """8. Total profit must strictly be the sum of accepted jobs; rejected high-profit jobs add 0."""
        jobs = [
            {"id": 801, "name": "Feasible-Job", "processing_time": 2.0, "burst_time": 2.0, "deadline": 4.0, "profit": 60.0, "priority": "High", "required_resource": "Employee"},
            {"id": 802, "name": "Impossible-Job", "processing_time": 10.0, "burst_time": 10.0, "deadline": 3.0, "profit": 9999.0, "priority": "High", "required_resource": "Employee"}
        ]
        resources = [self.standard_employee]

        for alg_name, scheduler in [("Greedy", greedy_job_scheduling), ("DP", dynamic_programming_job_scheduling)]:
            res = scheduler(jobs, resources)
            self.assertEqual(len(res["schedules"]), 1)
            self.assertEqual(res["schedules"][0]["id"], 801)
            self.assertEqual(res["metrics"]["total_profit"], 60.0)

    # --------------------------------------------------------------------------
    # 9. Empty job lists and zero-profit jobs
    # --------------------------------------------------------------------------
    def test_09_empty_and_zero_profit_jobs(self):
        """9. Empty job lists, zero-profit jobs, and zero capacity handled safely without DivisionByZero."""
        for alg_name, scheduler in [("Greedy", greedy_job_scheduling), ("DP", dynamic_programming_job_scheduling)]:
            empty_res = scheduler([], [])
            self.assertEqual(empty_res["metrics"]["total_jobs"], 0)
            self.assertEqual(empty_res["metrics"]["total_profit"], 0.0)
            self.assertEqual(empty_res["metrics"]["resource_utilization"], 0.0)

            # Zero-profit job should be schedulable if feasible
            zero_job = [{"id": 901, "name": "Zero-Profit", "processing_time": 2.0, "burst_time": 2.0, "deadline": 4.0, "profit": 0.0, "priority": "Low", "required_resource": "Employee"}]
            res = scheduler(zero_job, [self.standard_employee])
            self.assertEqual(len(res["schedules"]), 1)
            self.assertEqual(res["metrics"]["total_profit"], 0.0)
            self.assertTrue(validate_schedule(res["schedules"], [self.standard_employee], zero_job)["valid"])

    # --------------------------------------------------------------------------
    # 10. Greedy and exact optimizer return feasible schedules
    # --------------------------------------------------------------------------
    def test_10_greedy_and_dp_return_feasible_schedules(self):
        """10. Both algorithms produce schedules that pass all 8 strict validator constraints."""
        resources = [self.standard_employee, self.standard_machine]
        jobs = [
            {"id": 1001, "name": "J1", "processing_time": 3, "burst_time": 3, "deadline": 5, "profit": 50, "priority": "High", "required_resource": "Employee"},
            {"id": 1002, "name": "J2", "processing_time": 2, "burst_time": 2, "deadline": 4, "profit": 40, "priority": "Medium", "required_resource": "Machine"},
            {"id": 1003, "name": "J3", "processing_time": 4, "burst_time": 4, "deadline": 8, "profit": 70, "priority": "High", "required_resource": "Employee"}
        ]
        for alg_name, scheduler in [("Greedy", greedy_job_scheduling), ("DP", dynamic_programming_job_scheduling)]:
            res = scheduler(jobs, resources)
            val = validate_schedule(res["schedules"], resources, jobs)
            self.assertTrue(val["valid"], f"{alg_name} schedule validation failed: {val.get('error')}")

    # --------------------------------------------------------------------------
    # 11. Exact optimizer profit is at least as high as Greedy
    # --------------------------------------------------------------------------
    def test_11_exact_optimizer_profit_at_least_greedy(self):
        """11. The exact optimizer's profit is >= Greedy's profit on any valid problem instance."""
        resources = [self.standard_employee, self.standard_machine, self.standard_computer, self.second_employee]
        jobs = [
            {"id": 219, "name": "J001 Website Development", "processing_time": 3, "burst_time": 3, "deadline": 6, "profit": 90, "priority": "High", "required_resource": "Employee"},
            {"id": 220, "name": "J002 Database Backup", "processing_time": 2, "burst_time": 2, "deadline": 4, "profit": 80, "priority": "High", "required_resource": "Machine"},
            {"id": 221, "name": "J003 Software Testing", "processing_time": 4, "burst_time": 4, "deadline": 9, "profit": 120, "priority": "Medium", "required_resource": "Employee"},
            {"id": 222, "name": "J004 Documentation", "processing_time": 2, "burst_time": 2, "deadline": 5, "profit": 40, "priority": "Low", "required_resource": "Employee"},
            {"id": 223, "name": "J005 Server Maintenance", "processing_time": 3, "burst_time": 3, "deadline": 7, "profit": 110, "priority": "High", "required_resource": "Machine"},
            {"id": 224, "name": "J006 API Development", "processing_time": 5, "burst_time": 5, "deadline": 11, "profit": 150, "priority": "High", "required_resource": "Employee"},
            {"id": 225, "name": "J007 UI Design", "processing_time": 3, "burst_time": 3, "deadline": 7, "profit": 85, "priority": "Medium", "required_resource": "Employee"},
            {"id": 226, "name": "J008 Data Processing", "processing_time": 4, "burst_time": 4, "deadline": 10, "profit": 130, "priority": "High", "required_resource": "Computer"}
        ]
        g_res = greedy_job_scheduling(jobs, resources)
        dp_res = dynamic_programming_job_scheduling(jobs, resources)

        self.assertGreaterEqual(
            dp_res["metrics"]["total_profit"],
            g_res["metrics"]["total_profit"],
            f"DP profit ({dp_res['metrics']['total_profit']}) must be >= Greedy ({g_res['metrics']['total_profit']})"
        )

    # --------------------------------------------------------------------------
    # 12. Repeated runs on the same input produce consistent results
    # --------------------------------------------------------------------------
    def test_12_repeated_runs_produce_consistent_results(self):
        """12. Determinism check: 5 repeated executions yield identical schedules, profits, and job sequences."""
        resources = [self.standard_employee, self.standard_machine]
        jobs = [
            {"id": 1, "name": "A", "processing_time": 2, "burst_time": 2, "deadline": 4, "profit": 80, "priority": "High", "required_resource": "Employee"},
            {"id": 2, "name": "B", "processing_time": 3, "burst_time": 3, "deadline": 6, "profit": 90, "priority": "High", "required_resource": "Employee"},
            {"id": 3, "name": "C", "processing_time": 2, "burst_time": 2, "deadline": 5, "profit": 70, "priority": "Medium", "required_resource": "Machine"}
        ]
        for alg_name, scheduler in [("Greedy", greedy_job_scheduling), ("DP", dynamic_programming_job_scheduling)]:
            baseline = scheduler(jobs, resources)
            for _ in range(4):
                run = scheduler(jobs, resources)
                self.assertEqual(run["metrics"]["total_profit"], baseline["metrics"]["total_profit"])
                self.assertEqual(run["metrics"]["scheduled_count"], baseline["metrics"]["scheduled_count"])
                self.assertEqual([s["id"] for s in run["schedules"]], [s["id"] for s in baseline["schedules"]])
                self.assertEqual([(s["start_time"], s["end_time"]) for s in run["schedules"]],
                                 [(s["start_time"], s["end_time"]) for s in baseline["schedules"]])

    # --------------------------------------------------------------------------
    # 13. Small dataset where locally attractive Greedy leads to less profit than DP
    # --------------------------------------------------------------------------
    def test_13_greedy_suboptimal_vs_exact_optimizer(self):
        """13. Demonstrates why DP is useful: Greedy picks one large $100 job, blocking two $70 jobs ($140 total)."""
        resource = [dict(self.standard_employee, available_hours=8.0)]
        jobs = [
            # Job A: high single profit (100), duration 5. Consumes 5 of 8 hours.
            {"id": 131, "name": "Large-Greedy-Lure", "processing_time": 5.0, "burst_time": 5.0, "deadline": 8.0, "profit": 100.0, "priority": "High", "required_resource": "Employee"},
            # Job B: duration 4, profit 70
            {"id": 132, "name": "Pair-Job-1", "processing_time": 4.0, "burst_time": 4.0, "deadline": 8.0, "profit": 70.0, "priority": "High", "required_resource": "Employee"},
            # Job C: duration 4, profit 70
            {"id": 133, "name": "Pair-Job-2", "processing_time": 4.0, "burst_time": 4.0, "deadline": 8.0, "profit": 70.0, "priority": "High", "required_resource": "Employee"}
        ]

        greedy_res = greedy_job_scheduling(jobs, resource)
        dp_res = dynamic_programming_job_scheduling(jobs, resource)

        # Greedy sorts by profit: picks Job 131 (profit 100). Remaining 3h cannot fit 132 or 133 (need 4h each).
        self.assertEqual(greedy_res["metrics"]["total_profit"], 100.0)
        self.assertEqual(len(greedy_res["schedules"]), 1)
        self.assertEqual(greedy_res["schedules"][0]["id"], 131)

        # DP evaluates combinations: skips Job 131, schedules Job 132 + Job 133 (4h + 4h = 8h <= 8h, profit = 140.0)
        self.assertEqual(dp_res["metrics"]["total_profit"], 140.0)
        self.assertEqual(len(dp_res["schedules"]), 2)
        self.assertEqual(set(s["id"] for s in dp_res["schedules"]), {132, 133})

        # Proof of DP superiority over greedy heuristic
        self.assertGreater(dp_res["metrics"]["total_profit"], greedy_res["metrics"]["total_profit"])
        self.assertTrue(validate_schedule(dp_res["schedules"], resource, jobs)["valid"])
        self.assertTrue(validate_schedule(greedy_res["schedules"], resource, jobs)["valid"])

    # --------------------------------------------------------------------------
    # 14. Official 8-job dataset from the user application evaluated across 4 resources
    # --------------------------------------------------------------------------
    def test_14_eight_job_dataset_used_by_application(self):
        """14. Official 8-job dataset from the user application evaluated across 4 resources."""
        resources = [
            self.standard_employee,   # R001: Employee (8h)
            self.standard_machine,    # R002: Machine (12h)
            self.standard_computer,   # R003: Computer (16h)
            self.second_employee      # R004: Employee (8h)
        ]
        jobs = [
            {"id": 219, "name": "J001 Website Development", "processing_time": 3, "burst_time": 3, "deadline": 6, "profit": 90, "priority": "High", "required_resource": "Employee"},
            {"id": 220, "name": "J002 Database Backup", "processing_time": 2, "burst_time": 2, "deadline": 4, "profit": 80, "priority": "High", "required_resource": "Machine"},
            {"id": 221, "name": "J003 Software Testing", "processing_time": 4, "burst_time": 4, "deadline": 9, "profit": 120, "priority": "Medium", "required_resource": "Employee"},
            {"id": 222, "name": "J004 Documentation", "processing_time": 2, "burst_time": 2, "deadline": 5, "profit": 40, "priority": "Low", "required_resource": "Employee"},
            {"id": 223, "name": "J005 Server Maintenance", "processing_time": 3, "burst_time": 3, "deadline": 7, "profit": 110, "priority": "High", "required_resource": "Machine"},
            {"id": 224, "name": "J006 API Development", "processing_time": 5, "burst_time": 5, "deadline": 11, "profit": 150, "priority": "High", "required_resource": "Employee"},
            {"id": 225, "name": "J007 UI Design", "processing_time": 3, "burst_time": 3, "deadline": 7, "profit": 85, "priority": "Medium", "required_resource": "Employee"},
            {"id": 226, "name": "J008 Data Processing", "processing_time": 4, "burst_time": 4, "deadline": 10, "profit": 130, "priority": "High", "required_resource": "Computer"}
        ]

        dp_res = dynamic_programming_job_scheduling(jobs, resources)
        self.assertEqual(dp_res["metrics"]["total_jobs"], 8)
        self.assertEqual(dp_res["metrics"]["scheduled_count"], 7)
        self.assertEqual(dp_res["metrics"]["missed_count"], 1)
        self.assertEqual(dp_res["metrics"]["total_profit"], 765.0)
        self.assertEqual(dp_res["metrics"]["total_processing_time"], 24.0)
        self.assertEqual(dp_res["missed_jobs"][0]["id"], 222)
        self.assertEqual(dp_res["missed_jobs"][0]["missed_reason"], "NOT_SELECTED_BY_OPTIMIZER")

        # Independent schedule validation
        val = validate_schedule(dp_res["schedules"], resources, jobs)
        self.assertTrue(val["valid"], f"Schedule validation failed: {val.get('error')}")

    # --------------------------------------------------------------------------
    # 15. Agreement between selected-job list, profit, processing time, and DP result
    # --------------------------------------------------------------------------
    def test_15_agreement_between_selected_jobs_profit_and_dp_tables(self):
        """15. Verifies mathematical harmony: sum(scheduled profits) == metrics.total_profit == sum(resource DP optimal cells)."""
        resources = [self.standard_employee, self.standard_machine, self.standard_computer, self.second_employee]
        jobs = [
            {"id": 219, "name": "J001 Website Development", "processing_time": 3, "burst_time": 3, "deadline": 6, "profit": 90, "priority": "High", "required_resource": "Employee"},
            {"id": 220, "name": "J002 Database Backup", "processing_time": 2, "burst_time": 2, "deadline": 4, "profit": 80, "priority": "High", "required_resource": "Machine"},
            {"id": 221, "name": "J003 Software Testing", "processing_time": 4, "burst_time": 4, "deadline": 9, "profit": 120, "priority": "Medium", "required_resource": "Employee"},
            {"id": 222, "name": "J004 Documentation", "processing_time": 2, "burst_time": 2, "deadline": 5, "profit": 40, "priority": "Low", "required_resource": "Employee"},
            {"id": 223, "name": "J005 Server Maintenance", "processing_time": 3, "burst_time": 3, "deadline": 7, "profit": 110, "priority": "High", "required_resource": "Machine"},
            {"id": 224, "name": "J006 API Development", "processing_time": 5, "burst_time": 5, "deadline": 11, "profit": 150, "priority": "High", "required_resource": "Employee"},
            {"id": 225, "name": "J007 UI Design", "processing_time": 3, "burst_time": 3, "deadline": 7, "profit": 85, "priority": "Medium", "required_resource": "Employee"},
            {"id": 226, "name": "J008 Data Processing", "processing_time": 4, "burst_time": 4, "deadline": 10, "profit": 130, "priority": "High", "required_resource": "Computer"}
        ]

        dp_res = dynamic_programming_job_scheduling(jobs, resources)
        scheds = dp_res["schedules"]
        metrics = dp_res["metrics"]
        dp_grid = dp_res["dp_grid"]

        # A. Sum of selected job profits equals total profit
        computed_profit = sum(s["profit"] for s in scheds)
        self.assertEqual(computed_profit, metrics["total_profit"])
        self.assertEqual(metrics["total_profit"], 765.0)

        # B. Sum of selected job processing times equals total processing time
        computed_proc = sum(s["processing_time"] for s in scheds)
        self.assertEqual(computed_proc, metrics["total_processing_time"])
        self.assertEqual(metrics["total_processing_time"], 24.0)

        # C. Resource tables sum equals multi-resource profit
        res_tables = dp_grid.get("resource_tables", [])
        sum_resource_tables = sum(r_tab["optimal_profit"] for r_tab in res_tables)
        self.assertEqual(sum_resource_tables, metrics["total_profit"])

        # D. Theoretical single-timeline baseline is exactly 360
        self.assertEqual(dp_grid["single_timeline_profit"], 360)

    # --------------------------------------------------------------------------
    # 16. DP optimality against exhaustive enumeration for small instances
    # --------------------------------------------------------------------------
    def test_16_dp_optimality_against_exhaustive_enumeration(self):
        """16. Compares DP against exhaustive combinatorial search ground truth to verify exact optimality."""
        resources = [
            {"id": 1, "resource_id": "R001", "resource_name": "Dev", "resource_type": "Employee", "available_hours": 6.0, "status": "Available"},
            {"id": 2, "resource_id": "R002", "resource_name": "Node", "resource_type": "Machine", "available_hours": 8.0, "status": "Available"}
        ]
        jobs = [
            {"id": 101, "name": "E-Job1", "processing_time": 3, "burst_time": 3, "deadline": 6, "profit": 80, "priority": "High", "required_resource": "Employee"},
            {"id": 102, "name": "E-Job2", "processing_time": 3, "burst_time": 3, "deadline": 6, "profit": 75, "priority": "Medium", "required_resource": "Employee"},
            {"id": 103, "name": "E-Job3", "processing_time": 4, "burst_time": 4, "deadline": 5, "profit": 90, "priority": "High", "required_resource": "Employee"},
            {"id": 104, "name": "M-Job1", "processing_time": 4, "burst_time": 4, "deadline": 8, "profit": 110, "priority": "High", "required_resource": "Machine"},
            {"id": 105, "name": "M-Job2", "processing_time": 4, "burst_time": 4, "deadline": 8, "profit": 100, "priority": "Medium", "required_resource": "Machine"},
            {"id": 106, "name": "M-Job3", "processing_time": 5, "burst_time": 5, "deadline": 7, "profit": 120, "priority": "High", "required_resource": "Machine"},
        ]

        def exhaustive_max_profit(job_list):
            from itertools import combinations, permutations
            emp_jobs = [j for j in job_list if j["required_resource"] == "Employee"]
            mach_jobs = [j for j in job_list if j["required_resource"] == "Machine"]

            emp_best = 0
            for r in range(1, len(emp_jobs) + 1):
                for subset in combinations(emp_jobs, r):
                    for order in permutations(subset):
                        t = 0.0
                        feasible = True
                        for j in order:
                            if t + j["processing_time"] > j["deadline"] or t + j["processing_time"] > 6.0:
                                feasible = False
                                break
                            t += j["processing_time"]
                        if feasible:
                            emp_best = max(emp_best, sum(j["profit"] for j in order))

            mach_best = 0
            for r in range(1, len(mach_jobs) + 1):
                for subset in combinations(mach_jobs, r):
                    for order in permutations(subset):
                        t = 0.0
                        feasible = True
                        for j in order:
                            if t + j["processing_time"] > j["deadline"] or t + j["processing_time"] > 8.0:
                                feasible = False
                                break
                            t += j["processing_time"]
                        if feasible:
                            mach_best = max(mach_best, sum(j["profit"] for j in order))

            return emp_best + mach_best

        ground_truth_profit = exhaustive_max_profit(jobs)
        dp_res = dynamic_programming_job_scheduling(jobs, resources)

        # DP must achieve the exact combinatorial global optimum
        self.assertEqual(dp_res["metrics"]["total_profit"], ground_truth_profit,
                         f"DP profit ({dp_res['metrics']['total_profit']}) != ground truth ({ground_truth_profit})")
        
        # Valid output schedule
        self.assertTrue(validate_schedule(dp_res["schedules"], resources, jobs)["valid"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
