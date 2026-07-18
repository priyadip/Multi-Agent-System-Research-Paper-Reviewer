"""
Evaluation harness for the multi-agent paper reviewer.
"""

import json
import time
import sys
import os
from typing import Dict, Any, List

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.orchestrator import PaperReviewOrchestrator


class EvaluationHarness:
    """Harness for evaluating the multi-agent system."""
    
    def __init__(self, test_cases_file: str = "test_cases.json"):
        """Initialize the evaluation harness."""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.test_cases_file = os.path.join(base_dir, test_cases_file)
        
        self.test_cases = self._load_test_cases()
        self.orchestrator = PaperReviewOrchestrator()
        self.results = []
    
    def _load_test_cases(self) -> List[Dict[str, Any]]:
        """Load test cases from JSON file."""
        try:
            with open(self.test_cases_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: Test cases file '{self.test_cases_file}' not found")
            return []
    
    def check_constraints(self, result: Dict[str, Any], 
                         constraints: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if result meets constraints.
        
        Args:
            result: Review result
            constraints: Constraint specifications
            
        Returns:
            Dictionary of constraint violations
        """
        violations = {}
        
        # Check duration
        if "max_duration_seconds" in constraints:
            duration = result.get("metrics", {}).get("duration_seconds", 0)
            if duration > constraints["max_duration_seconds"]:
                violations["duration"] = {
                    "expected": f"<= {constraints['max_duration_seconds']}s",
                    "actual": f"{duration:.2f}s"
                }
        
        # Check tool calls
        if "min_tool_calls" in constraints:
            tool_calls = result.get("metrics", {}).get("total_tool_calls", 0)
            if tool_calls < constraints["min_tool_calls"]:
                violations["min_tool_calls"] = {
                    "expected": f">= {constraints['min_tool_calls']}",
                    "actual": tool_calls
                }
        
        if "max_tool_calls" in constraints:
            tool_calls = result.get("metrics", {}).get("total_tool_calls", 0)
            if tool_calls > constraints["max_tool_calls"]:
                violations["max_tool_calls"] = {
                    "expected": f"<= {constraints['max_tool_calls']}",
                    "actual": tool_calls
                }
        
        # Check required fields
        if "required_fields" in constraints:
            for field in constraints["required_fields"]:
                if field not in result:
                    violations[f"missing_field_{field}"] = {
                        "expected": "present",
                        "actual": "missing"
                    }
        
        return violations
    
    def run_test_case(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run a single test case.
        
        Args:
            test_case: Test case specification
            
        Returns:
            Test result
        """
        test_id = test_case["test_id"]
        arxiv_id = test_case["arxiv_id"]
        expected_status = test_case["expected_status"]
        constraints = test_case.get("constraints", {})
        
        print(f"\nRunning {test_id}: {test_case['name']}")
        print(f"  arXiv ID: {arxiv_id}")
        
        start_time = time.time()
        
        try:
            # Run review
            result = self.orchestrator.review_paper(arxiv_id)
            actual_status = result.get("status", "unknown")
            
            # Check if status matches expectation
            status_match = actual_status == expected_status
            
            # Check constraints
            violations = self.check_constraints(result, constraints) if actual_status == "success" else {}
            
            # Determine pass/fail
            passed = status_match and len(violations) == 0
            
            test_result = {
                "test_id": test_id,
                "name": test_case["name"],
                "arxiv_id": arxiv_id,
                "expected_status": expected_status,
                "actual_status": actual_status,
                "status_match": status_match,
                "passed": passed,
                "violations": violations,
                "duration": time.time() - start_time,
                "result": result
            }
            
            print(f"  Status: {'✓ PASS' if passed else '✗ FAIL'}")
            if violations:
                print(f"  Violations: {len(violations)}")
            
            return test_result
            
        except Exception as e:
            print(f"  Status: ✗ ERROR - {str(e)}")
            return {
                "test_id": test_id,
                "name": test_case["name"],
                "arxiv_id": arxiv_id,
                "expected_status": expected_status,
                "actual_status": "error",
                "status_match": expected_status == "error",
                "passed": False,
                "violations": {"exception": str(e)},
                "duration": time.time() - start_time,
                "result": {"error": str(e)}
            }
    
    def run_all_tests(self) -> Dict[str, Any]:
        """
        Run all test cases.
        
        Returns:
            Summary of all test results
        """
        print("="*60)
        print("Starting Evaluation Harness")
        print("="*60)
        print(f"Total test cases: {len(self.test_cases)}")
        
        for test_case in self.test_cases:
            result = self.run_test_case(test_case)
            self.results.append(result)
        
        # Compute summary metrics
        summary = self.compute_metrics()
        
        return summary
    
    def compute_metrics(self) -> Dict[str, Any]:
        """
        Compute evaluation metrics.
        
        Returns:
            Dictionary of metrics
        """
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r["passed"])
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Compute average latency for successful tests
        successful_results = [r for r in self.results if r["actual_status"] == "success"]
        avg_latency = (sum(r["duration"] for r in successful_results) / len(successful_results)) if successful_results else 0
        
        # Compute average tool calls
        avg_tool_calls = 0
        if successful_results:
            tool_call_counts = [
                r["result"].get("metrics", {}).get("total_tool_calls", 0)
                for r in successful_results
            ]
            avg_tool_calls = sum(tool_call_counts) / len(tool_call_counts) if tool_call_counts else 0
        
        # Count constraint violations
        total_violations = sum(len(r["violations"]) for r in self.results)
        
        summary = {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "success_rate": success_rate,
            "average_latency_seconds": avg_latency,
            "average_tool_calls": avg_tool_calls,
            "total_constraint_violations": total_violations,
            "test_results": self.results
        }
        
        return summary
    
    def print_summary(self, summary: Dict[str, Any]):
        """Print evaluation summary."""
        print("\n" + "="*60)
        print("EVALUATION SUMMARY")
        print("="*60)
        print(f"Total Tests:        {summary['total_tests']}")
        print(f"Passed:             {summary['passed']}")
        print(f"Failed:             {summary['failed']}")
        print(f"Success Rate:       {summary['success_rate']:.2f}%")
        print(f"Avg Latency:        {summary['average_latency_seconds']:.2f}s")
        print(f"Avg Tool Calls:     {summary['average_tool_calls']:.2f}")
        print(f"Constraint Violations: {summary['total_constraint_violations']}")
        print("="*60)
    
    def save_results(self, filename: str = "eval_results.json"):
        """Save results to file."""
        summary = self.compute_metrics()
        
        with open(filename, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\nResults saved to: {filename}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run evaluation harness")
    parser.add_argument("--test-cases", default="test_cases.json", help="Test cases file")
    parser.add_argument("--output", default="eval_results.json", help="Output file")
    
    args = parser.parse_args()
    
    # Run evaluation
    harness = EvaluationHarness(args.test_cases)
    summary = harness.run_all_tests()
    
    # Print summary
    harness.print_summary(summary)
    
    # Save results
    harness.save_results(args.output)


if __name__ == "__main__":
    main()