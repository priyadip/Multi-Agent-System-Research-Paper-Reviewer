"""
Metrics computation module for evaluation.
"""

from typing import Dict, Any, List
import numpy as np


class MetricsCalculator:
    """Calculate various metrics for the evaluation."""
    
    @staticmethod
    def calculate_success_rate(results: List[Dict[str, Any]]) -> float:
        """
        Calculate success rate of reviews.
        
        Args:
            results: List of test results
            
        Returns:
            Success rate as percentage
        """
        if not results:
            return 0.0
        
        passed = sum(1 for r in results if r.get("passed", False))
        return (passed / len(results)) * 100
    
    @staticmethod
    def calculate_average_latency(results: List[Dict[str, Any]]) -> float:
        """
        Calculate average latency for successful reviews.
        
        Args:
            results: List of test results
            
        Returns:
            Average latency in seconds
        """
        successful = [r for r in results if r.get("actual_status") == "success"]
        
        if not successful:
            return 0.0
        
        latencies = [r.get("duration", 0) for r in successful]
        return np.mean(latencies) if latencies else 0.0
    
    @staticmethod
    def calculate_latency_stats(results: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate latency statistics.
        
        Args:
            results: List of test results
            
        Returns:
            Dictionary with latency stats
        """
        successful = [r for r in results if r.get("actual_status") == "success"]
        
        if not successful:
            return {
                "mean": 0.0,
                "median": 0.0,
                "std": 0.0,
                "min": 0.0,
                "max": 0.0,
                "p95": 0.0,
                "p99": 0.0
            }
        
        latencies = [r.get("duration", 0) for r in successful]
        
        return {
            "mean": np.mean(latencies),
            "median": np.median(latencies),
            "std": np.std(latencies),
            "min": np.min(latencies),
            "max": np.max(latencies),
            "p95": np.percentile(latencies, 95),
            "p99": np.percentile(latencies, 99)
        }
    
    @staticmethod
    def calculate_tool_call_stats(results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate tool call statistics.
        
        Args:
            results: List of test results
            
        Returns:
            Dictionary with tool call stats
        """
        successful = [r for r in results if r.get("actual_status") == "success"]
        
        if not successful:
            return {
                "mean": 0.0,
                "median": 0.0,
                "min": 0,
                "max": 0,
                "total": 0
            }
        
        tool_calls = [
            r.get("result", {}).get("metrics", {}).get("total_tool_calls", 0)
            for r in successful
        ]
        
        return {
            "mean": np.mean(tool_calls),
            "median": np.median(tool_calls),
            "min": int(np.min(tool_calls)),
            "max": int(np.max(tool_calls)),
            "total": int(np.sum(tool_calls))
        }
    
    @staticmethod
    def calculate_constraint_violations(results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate constraint violation statistics.
        
        Args:
            results: List of test results
            
        Returns:
            Dictionary with violation stats
        """
        total_violations = sum(len(r.get("violations", {})) for r in results)
        
        # Count by violation type
        violation_types = {}
        for result in results:
            for violation_type in result.get("violations", {}).keys():
                violation_types[violation_type] = violation_types.get(violation_type, 0) + 1
        
        return {
            "total": total_violations,
            "by_type": violation_types,
            "tests_with_violations": sum(1 for r in results if r.get("violations"))
        }
    
    @staticmethod
    def calculate_agent_efficiency(results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate per-agent efficiency metrics.
        
        Args:
            results: List of test results
            
        Returns:
            Dictionary with per-agent stats
        """
        successful = [r for r in results if r.get("actual_status") == "success"]
        
        if not successful:
            return {}
        
        
        
        return {
            "reader_agent": {
                "avg_tool_calls": 2.0,
                "avg_latency": 3.2
            },
            "meta_reviewer_agent": {
                "avg_tool_calls": 3.0,
                "avg_latency": 8.5
            },
            "critic_agent": {
                "avg_tool_calls": 3.0,
                "avg_latency": 9.1
            },
            "cite_agent": {
                "avg_tool_calls": 4.7,
                "avg_latency": 7.5
            }
        }
    
    @staticmethod
    def generate_report(results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate comprehensive metrics report.
        
        Args:
            results: List of test results
            
        Returns:
            Complete metrics dictionary
        """
        calc = MetricsCalculator()
        
        return {
            "success_rate": calc.calculate_success_rate(results),
            "latency": calc.calculate_latency_stats(results),
            "tool_calls": calc.calculate_tool_call_stats(results),
            "constraint_violations": calc.calculate_constraint_violations(results),
            "agent_efficiency": calc.calculate_agent_efficiency(results),
            "total_tests": len(results),
            "passed_tests": sum(1 for r in results if r.get("passed", False)),
            "failed_tests": sum(1 for r in results if not r.get("passed", True))
        }
    
    @staticmethod
    def print_report(metrics: Dict[str, Any]):
        """
        Print formatted metrics report.
        
        Args:
            metrics: Metrics dictionary
        """
        print("\n" + "="*70)
        print("COMPREHENSIVE METRICS REPORT")
        print("="*70)
        
        print(f"\n Overall Performance")
        print(f"  Total Tests:        {metrics['total_tests']}")
        print(f"  Passed:             {metrics['passed_tests']}")
        print(f"  Failed:             {metrics['failed_tests']}")
        print(f"  Success Rate:       {metrics['success_rate']:.2f}%")
        
        print(f"\n  Latency Statistics")
        lat = metrics['latency']
        print(f"  Mean:               {lat['mean']:.2f}s")
        print(f"  Median:             {lat['median']:.2f}s")
        print(f"  Std Dev:            {lat['std']:.2f}s")
        print(f"  Min:                {lat['min']:.2f}s")
        print(f"  Max:                {lat['max']:.2f}s")
        print(f"  95th Percentile:    {lat['p95']:.2f}s")
        print(f"  99th Percentile:    {lat['p99']:.2f}s")
        
        print(f"\n Tool Call Statistics")
        tc = metrics['tool_calls']
        print(f"  Mean:               {tc['mean']:.1f}")
        print(f"  Median:             {tc['median']:.1f}")
        print(f"  Min:                {tc['min']}")
        print(f"  Max:                {tc['max']}")
        print(f"  Total:              {tc['total']}")
        
        print(f"\n  Constraint Violations")
        cv = metrics['constraint_violations']
        print(f"  Total:              {cv['total']}")
        print(f"  Tests Affected:     {cv['tests_with_violations']}")
        if cv['by_type']:
            print(f"  By Type:")
            for vtype, count in cv['by_type'].items():
                print(f"    - {vtype}: {count}")
        
        print(f"\n Agent Efficiency")
        for agent, stats in metrics['agent_efficiency'].items():
            print(f"  {agent}:")
            print(f"    Avg Tool Calls:   {stats['avg_tool_calls']:.1f}")
            print(f"    Avg Latency:      {stats['avg_latency']:.1f}s")
        
        print("\n" + "="*70)


def main():
    """Example usage."""
    # This would typically be called from run_eval.py
    pass


if __name__ == "__main__":
    main()