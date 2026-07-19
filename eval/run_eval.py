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
from eval.metrics import MetricsCalculator


class EvaluationHarness:
    """Harness for evaluating the multi-agent system."""
    
    def __init__(self, test_cases_file: str = "test_cases.json"):
        """Initialize the evaluation harness."""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.test_cases_file = os.path.join(base_dir, test_cases_file)
        
        self.test_cases = self._load_test_cases()

        # The orchestrator needs a Groq API key. base_agent loads .env on import,
        # so GROQ_API_KEY / MODEL_NAME from a local .env are picked up here.
        api_key = os.getenv("GROQ_API_KEY")
        model = os.getenv("MODEL_NAME")
        if not api_key:
            print("Warning: GROQ_API_KEY is not set. Reviews will fail until you "
                  "set it (e.g. in a .env file or the environment).")
        self.orchestrator = PaperReviewOrchestrator(api_key=api_key, model=model)
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

    # Signatures that an agent's LLM call failed and returned an error string
    # instead of real content (see base_agent.call_llm / llm_pool.chat).
    ERROR_MARKERS = (
        "invalid api key", "invalid_api_key", "error code:",
        "all providers failed", "no groq api key", "rate limit",
    )

    def _llm_error_markers(self, result: Dict[str, Any]) -> List[str]:
        """Return which LLM-error signatures appear in the report content.

        A review that is 'success' at the structural level can still be garbage
        if every LLM call failed (e.g. a bad API key). We scan the report text
        (excluding the paper's own full_text, which may legitimately contain the
        word 'error') for known failure signatures.
        """
        probe = dict(result)
        probe.pop("full_text", None)
        blob = json.dumps(probe, default=str).lower()
        return [m for m in self.ERROR_MARKERS if m in blob]

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

            # A structurally-successful review is only real if its content is not
            # just LLM error strings. This catches broken keys / rate-limit runs
            # that would otherwise be counted as passing.
            if actual_status == "success":
                markers = self._llm_error_markers(result)
                if markers:
                    violations["llm_errors"] = {
                        "expected": "review text free of LLM error markers",
                        "actual": ", ".join(sorted(set(markers)))
                    }

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
            
            print(f"  Status: {'PASS' if passed else 'FAIL'}")
            if violations:
                print(f"  Violations: {len(violations)}")

            return test_result

        except Exception as e:
            print(f"  Status: ERROR - {str(e)}")
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

        # Single source of truth for metrics: MetricsCalculator.
        return MetricsCalculator.generate_report(self.results)

    def compute_metrics(self) -> Dict[str, Any]:
        """Backward-compatible alias for the full metrics report."""
        return MetricsCalculator.generate_report(self.results)

    def print_summary(self, summary: Dict[str, Any]):
        """Print the full metrics report."""
        MetricsCalculator.print_report(summary)

    @staticmethod
    def _slim_result(r: Dict[str, Any]) -> Dict[str, Any]:
        """Drop the bulky extracted full text so saved JSON stays small."""
        slim = dict(r)
        result = slim.get("result")
        if isinstance(result, dict) and "full_text" in result:
            result = dict(result)
            result["full_text"] = f"<omitted: {len(result['full_text'])} chars>"
            slim["result"] = result
        return slim

    def save_results(self, filename: str = "eval_results.json"):
        """Save the metrics report plus per-test results (full text stripped)."""
        payload = {
            "summary": MetricsCalculator.generate_report(self.results),
            "test_results": [self._slim_result(r) for r in self.results],
        }
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

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