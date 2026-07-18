"""
Example usage script demonstrating the Multi-Agent Paper Reviewer system.
This script shows various ways to use the system.
"""

import sys
import os
import json
from typing import Dict, Any

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.orchestrator import PaperReviewOrchestrator
from agents.reader_agent import ReaderAgent


def example_1_basic_review():
    """Example 1: Basic paper review."""
    print("\n" + "="*70)
    print("EXAMPLE 1: Basic Paper Review")
    print("="*70)
    
    # Create orchestrator
    orchestrator = PaperReviewOrchestrator()
    
    # Review a paper
    arxiv_id = "1706.03762"  # Attention is All You Need
    print(f"\nReviewing paper: {arxiv_id}")
    
    result = orchestrator.review_paper(arxiv_id)
    
    # Print results
    if result["status"] == "success":
        print(f"\n Review completed successfully!")
        print(f"\nPaper: {result['paper_title']}")
        print(f"Authors: {', '.join(result['authors'][:3])}...")
        print(f"Duration: {result['metrics']['duration_seconds']:.2f}s")
        print(f"Tool Calls: {result['metrics']['total_tool_calls']}")
    else:
        print(f"\n Error: {result.get('error')}")
    
    return result


def example_2_metadata_only():
    """Example 2: Get paper metadata only (faster)."""
    print("\n" + "="*70)
    print("EXAMPLE 2: Quick Metadata Retrieval")
    print("="*70)
    
    # Create reader agent
    reader = ReaderAgent()
    
    # Get metadata
    arxiv_id = "2301.07041"
    print(f"\nFetching metadata for: {arxiv_id}")
    
    metadata = reader.fetch_paper_metadata(arxiv_id)
    
    # Print metadata
    print(f"\nTitle: {metadata.get('title', 'N/A')}")
    print(f"Authors: {len(metadata.get('authors', []))} authors")
    print(f"Published: {metadata.get('published', 'N/A')}")
    print(f"Categories: {', '.join(metadata.get('categories', []))}")
    print(f"\nAbstract (first 200 chars):")
    print(f"{metadata.get('abstract', 'N/A')[:200]}...")
    
    return metadata


def example_3_batch_review():
    """Example 3: Batch review multiple papers."""
    print("\n" + "="*70)
    print("EXAMPLE 3: Batch Review Multiple Papers")
    print("="*70)
    
    # List of papers to review
    paper_ids = [
        "1706.03762",  # Attention is All You Need
        "1810.04805",  # BERT
        "2005.14165"   # GPT-3
    ]
    
    orchestrator = PaperReviewOrchestrator()
    results = []
    
    for i, arxiv_id in enumerate(paper_ids, 1):
        print(f"\n[{i}/{len(paper_ids)}] Reviewing: {arxiv_id}")
        
        try:
            result = orchestrator.review_paper(arxiv_id)
            results.append({
                "arxiv_id": arxiv_id,
                "status": result["status"],
                "title": result.get("paper_title", "N/A"),
                "duration": result.get("metrics", {}).get("duration_seconds", 0)
            })
            print(f"   Completed in {results[-1]['duration']:.2f}s")
        except Exception as e:
            print(f"   Error: {str(e)}")
            results.append({
                "arxiv_id": arxiv_id,
                "status": "error",
                "error": str(e)
            })
    
    # Print summary
    print(f"\n{'='*70}")
    print("BATCH REVIEW SUMMARY")
    print(f"{'='*70}")
    
    for result in results:
        status_icon = "✓" if result["status"] == "success" else "✗"
        
        print(f"{status_icon} {result['arxiv_id']}: {result.get('title', result.get('error', 'Unknown'))}")
    
    total_time = sum(r.get('duration', 0) for r in results)
    print(f"\nTotal time: {total_time:.2f}s")
    print(f"Average time: {total_time/len(results):.2f}s per paper")
    
    return results


def example_4_extract_specific_info():
    """Example 4: Extract specific information from review."""
    print("\n" + "="*70)
    print("EXAMPLE 4: Extract Specific Information")
    print("="*70)
    
    orchestrator = PaperReviewOrchestrator()
    arxiv_id = "1706.03762"
    
    print(f"\nReviewing and extracting key info from: {arxiv_id}")
    result = orchestrator.review_paper(arxiv_id)
    
    if result["status"] == "success":
        # Extract specific information
        print(f"\n PAPER OVERVIEW")
        print(f"Title: {result['paper_title']}")
        print(f"Field: {', '.join(result['categories'][:2])}")
        
        print(f"\n TOP STRENGTHS:")
        for i, strength in enumerate(result['critical_analysis']['strengths'][:3], 1):
            print(f"{i}. {strength}")
        
        print(f"\n TOP WEAKNESSES:")
        for i, weakness in enumerate(result['critical_analysis']['weaknesses'][:3], 1):
            print(f"{i}. {weakness}")
        
        print(f"\n CITATION INFO:")
        print(f"Citations found: {result['citation_analysis']['citation_count']}")
        
        print(f"\n KEY TAKEAWAY:")
        # Extract first few sentences of overall review
        review_text = result['meta_review']['overall_review']
        takeaway = '. '.join(review_text.split('.')[:2]) + '.'
        print(f"{takeaway}")
    
    return result


def example_5_save_formatted_report():
    """Example 5: Save a formatted report."""
    print("\n" + "="*70)
    print("EXAMPLE 5: Save Formatted Report")
    print("="*70)
    
    orchestrator = PaperReviewOrchestrator()
    arxiv_id = "1706.03762"
    
    print(f"\nReviewing: {arxiv_id}")
    result = orchestrator.review_paper(arxiv_id)
    
    if result["status"] == "success":
        # Create markdown report
        report = f"""# Paper Review: {result['paper_title']}

## Metadata
- **arXiv ID**: {result['arxiv_id']}
- **Authors**: {', '.join(result['authors'][:5])}
- **Categories**: {', '.join(result['categories'])}

## Summary
{result['summary']['key_points']['summary']}

## Meta-Review
{result['meta_review']['overall_review']}

## Strengths
{chr(10).join(f"- {s}" for s in result['critical_analysis']['strengths'])}

## Weaknesses
{chr(10).join(f"- {w}" for w in result['critical_analysis']['weaknesses'])}

## Suggested Improvements
{result['critical_analysis']['improvements']}

## Citation Analysis
- **Citations found**: {result['citation_analysis']['citation_count']}
- **Recommendations**: {result['citation_analysis']['recommendations']}

## Review Metrics
- **Duration**: {result['metrics']['duration_seconds']:.2f}s
- **Tool Calls**: {result['metrics']['total_tool_calls']}
- **Agents Used**: {result['metrics']['agents_executed']}

---
*Generated by Multi-Agent Paper Reviewer*
"""
        
        # Save report
        filename = f"review_{arxiv_id}.md"
        with open(filename, 'w') as f:
            f.write(report)
        
        print(f"\n Report saved to: {filename}")
        
        # Also save JSON
        json_filename = f"review_{arxiv_id}.json"
        with open(json_filename, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f" JSON data saved to: {json_filename}")
    
    return result


def example_6_compare_papers():
    """Example 6: Compare multiple papers."""
    print("\n" + "="*70)
    print("EXAMPLE 6: Compare Papers Side-by-Side")
    print("="*70)
    
    papers = {
        "Transformers": "1706.03762",
        "BERT": "1810.04805"
    }
    
    orchestrator = PaperReviewOrchestrator()
    comparisons = {}
    
    for name, arxiv_id in papers.items():
        print(f"\nReviewing {name} ({arxiv_id})...")
        result = orchestrator.review_paper(arxiv_id)
        
        if result["status"] == "success":
            comparisons[name] = {
                "title": result["paper_title"],
                "strengths_count": len(result['critical_analysis']['strengths']),
                "weaknesses_count": len(result['critical_analysis']['weaknesses']),
                "citations": result['citation_analysis']['citation_count'],
                "processing_time": result['metrics']['duration_seconds']
            }
    
    # Print comparison
    print(f"\n{'='*70}")
    print("COMPARISON RESULTS")
    print(f"{'='*70}")
    
    print(f"\n{'Metric':<25} {'Transformers':<20} {'BERT':<20}")
    print("-" * 70)
    
    if comparisons:
        for metric in ["strengths_count", "weaknesses_count", "citations", "processing_time"]:
            values = [str(comparisons.get(name, {}).get(metric, "N/A")) for name in papers.keys()]
            print(f"{metric:<25} {values[0]:<20} {values[1]:<20}")
    
    return comparisons


def main():
    """Run all examples."""
    print("\n" + "="*70)
    print("MULTI-AGENT PAPER REVIEWER - EXAMPLE USAGE")
    print("="*70)
    print("\nThis script demonstrates various ways to use the system.")
    print("Each example will run automatically. Press Ctrl+C to stop.\n")
    
    try:
        # Run examples
        input("Press Enter to run Example 1: Basic Review...")
        example_1_basic_review()
        
        input("\nPress Enter to run Example 2: Metadata Only...")
        example_2_metadata_only()
        
        input("\nPress Enter to run Example 3: Batch Review (will take ~2 minutes)...")
        example_3_batch_review()
        
        input("\nPress Enter to run Example 4: Extract Specific Info...")
        example_4_extract_specific_info()
        
        input("\nPress Enter to run Example 5: Save Formatted Report...")
        example_5_save_formatted_report()
        
        input("\nPress Enter to run Example 6: Compare Papers (will take ~1 minute)...")
        example_6_compare_papers()
        
        print("\n" + "="*70)
        print("ALL EXAMPLES COMPLETED!")
        print("="*70)
        print("\nCheck the generated files:")
        print("  - review_*.md (Markdown reports)")
        print("  - review_*.json (JSON data)")
        
    except KeyboardInterrupt:
        print("\n\nExamples interrupted by user.")
    except Exception as e:
        print(f"\n\nError: {str(e)}")
        print("Make sure you have:")
        print("1. Set GROQ_API_KEY in .env file")
        print("2. Installed all requirements")
        print("3. Run setup.py to create project structure")


if __name__ == "__main__":
    main()