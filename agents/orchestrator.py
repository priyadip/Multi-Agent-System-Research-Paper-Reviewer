"""
Multi-Agent Orchestrator using LangGraph.
"""

import sys
from pathlib import Path

# Add project root to sys.path if running as script
if __name__ == "__main__" and __package__ is None:
    project_root = str(Path(__file__).resolve().parent.parent)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

import time
from typing import Dict, Any, TypedDict
from langgraph.graph import StateGraph, END

# Import all agents
from agents.reader_agent import ReaderAgent
from agents.meta_reviewer_agent import MetaReviewerAgent
from agents.critic_agent import CriticAgent
from agents.cite_agent import CiteAgent
# --- NEW IMPORTS ---
from agents.publication_agent import PublicationAgent



class ReviewState(TypedDict):
    """State for the review workflow."""
    arxiv_id: str
    reader_output: Dict[str, Any]
    meta_reviewer_output: Dict[str, Any]
    critic_output: Dict[str, Any]
    cite_output: Dict[str, Any]
    # --- NEW STATE FIELDS ---
    publication_output: Dict[str, Any]
   
    
    final_report: Dict[str, Any]
    error: str
    start_time: float
    end_time: float


class PaperReviewOrchestrator:
    """Orchestrates the multi-agent paper review workflow."""
    
    def __init__(self, api_key: str = None, model: str = None):
        """Initialize the orchestrator with all agents.

        Args:
            api_key: Groq API key passed to every agent. On the public app this
                     comes from the user's pasted key (per session, not stored).
                     Falls back to the GROQ_API_KEY env var when omitted.
            model:   Groq model id to use for every agent (e.g.
                     "llama-3.3-70b-versatile"). Falls back to the MODEL_NAME env
                     var, then to llama-3.1-8b-instant, when omitted.
        """
        self.reader_agent = ReaderAgent(api_key=api_key, model=model)
        self.meta_reviewer_agent = MetaReviewerAgent(api_key=api_key, model=model)
        self.critic_agent = CriticAgent(api_key=api_key, model=model)
        self.cite_agent = CiteAgent(api_key=api_key, model=model)
        # --- INITIALIZE NEW AGENTS ---
        self.publication_agent = PublicationAgent(api_key=api_key, model=model)
        
        
        # Build the workflow graph
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow."""
        # Define the graph
        workflow = StateGraph(ReviewState)
        
        # Add nodes for each agent
        workflow.add_node("reader", self._reader_node)
        workflow.add_node("publication", self._publication_node)  # <--- NEW
        
        workflow.add_node("meta_reviewer", self._meta_reviewer_node)
        workflow.add_node("critic", self._critic_node)
        workflow.add_node("cite", self._cite_node)
        workflow.add_node("finalize", self._finalize_node)
        
        # Define the workflow edges (Linear Flow)
        workflow.set_entry_point("reader")
        workflow.add_edge("reader", "publication")    # Reader -> Publication
        # Directly continue to meta_reviewer from publication (no discussion node)
        workflow.add_edge("publication", "meta_reviewer")
        workflow.add_edge("meta_reviewer", "critic")
        workflow.add_edge("critic", "cite")
        workflow.add_edge("cite", "finalize")
        workflow.add_edge("finalize", END)
        
        return workflow.compile()
    
    # --- NODE FUNCTIONS ---

    def _reader_node(self, state: ReviewState) -> ReviewState:
        print(f"\n[ReaderAgent] Processing paper: {state['arxiv_id']}")
        input_data = {"arxiv_id": state["arxiv_id"]}
        output = self.reader_agent.process(input_data)
        state["reader_output"] = output
        if output.get("output", {}).get("status") == "error":
            state["error"] = output["output"]["message"]
        print(f"[ReaderAgent] Tool calls: {output.get('tool_calls', 0)}")
        return state

    def _publication_node(self, state: ReviewState) -> ReviewState:
        """Execute Publication Agent"""
        print("\n[PublicationAgent] Searching for venue...")
        if state.get("error"): return state
        
        input_data = {"reader_output": state["reader_output"]}
        output = self.publication_agent.process(input_data)
        state["publication_output"] = output
        print(f"[PublicationAgent] Tool calls: {output.get('tool_calls', 0)}")
        return state



    def _meta_reviewer_node(self, state: ReviewState) -> ReviewState:
        print("\n[MetaReviewerAgent] Analyzing paper quality...")
        if state.get("error"): return state
        input_data = state["reader_output"]["output"]
        output = self.meta_reviewer_agent.process(input_data)
        state["meta_reviewer_output"] = output
        print(f"[MetaReviewerAgent] Tool calls: {output.get('tool_calls', 0)}")
        return state
    
    def _critic_node(self, state: ReviewState) -> ReviewState:
        print("\n[CriticAgent] Performing critical analysis...")
        if state.get("error"): return state
        
        # Note: We fixed the passing of reader_output here
        input_data = {
            "reader_output": state["reader_output"],
            "meta_reviewer_output": state["meta_reviewer_output"]
        }
        output = self.critic_agent.process(input_data)
        state["critic_output"] = output
        print(f"[CriticAgent] Tool calls: {output.get('tool_calls', 0)}")
        return state
    
    def _cite_node(self, state: ReviewState) -> ReviewState:
        print("\n[CiteAgent] Analyzing citations...")
        if state.get("error"): return state
        input_data = {"reader_output": state["reader_output"]}
        output = self.cite_agent.process(input_data)
        state["cite_output"] = output
        print(f"[CiteAgent] Tool calls: {output.get('tool_calls', 0)}")
        return state
    
    def _finalize_node(self, state: ReviewState) -> ReviewState:
        """Finalize the review and create report."""
        print("\n[Orchestrator] Finalizing review report...")
        state["end_time"] = time.time()
        
        if state.get("error"):
            state["final_report"] = {
                "status": "error",
                "error": state["error"],
                "duration": state["end_time"] - state["start_time"]
            }
            return state
        
        # Compile final report
        reader_data = state["reader_output"]["output"]
        meta_data = state["meta_reviewer_output"]["output"]
        critic_data = state["critic_output"]["output"]
        cite_data = state["cite_output"]["output"]
        # --- NEW DATA ---
        pub_data = state["publication_output"].get("output", {})
        
        
        total_tool_calls = (
            state["reader_output"].get("tool_calls", 0) +
            state["meta_reviewer_output"].get("tool_calls", 0) +
            state["critic_output"].get("tool_calls", 0) +
            state["cite_output"].get("tool_calls", 0) +
            state["publication_output"].get("tool_calls", 0) 
        )
         
        
        final_report = {
            "status": "success",
            "arxiv_id": state["arxiv_id"],
            "paper_title": reader_data.get("paper_title", "Unknown"),
            "authors": reader_data.get("authors", []),
            "categories": reader_data.get("categories", []),
            
            "summary": {
                "key_points": reader_data.get("key_points", {}),
                "abstract": reader_data.get("metadata", {}).get("abstract", "")
            },
            
            "meta_review": {
                "methodology": meta_data.get("methodology_analysis", {}),
                "contribution": meta_data.get("contribution_evaluation", {}),
                "overall_review": meta_data.get("overall_review", "")
            },
            
            "critical_analysis": {
                "strengths": critic_data.get("strengths", []),
                "weaknesses": critic_data.get("weaknesses", []),
                "improvements": critic_data.get("improvements", ""),
                "summary": critic_data.get("critique_summary", "")
            },
            
            "citation_analysis": {
                "citation_count": cite_data.get("citation_count", 0),
                "total_references": cite_data.get("total_references", 0),
                "reference_detection_method": cite_data.get("reference_detection_method", ""),
                "in_text_citation_count": cite_data.get("in_text_citation_count", 0),
                "in_text_citations": cite_data.get("in_text_citations", []),
                "context": cite_data.get("citation_context", {}),
                "quality": cite_data.get("reference_quality", {}),
                "recommendations": cite_data.get("recommendations", "")
            },
            
            # --- ADD NEW SECTIONS TO REPORT ---
            "publication_info": pub_data,
            
            
            "metrics": {
                "total_tool_calls": total_tool_calls,
                "duration_seconds": state["end_time"] - state["start_time"],
                "agents_executed": 5  # Now 5 agents (reader, publication, meta_reviewer, critic, cite)
            }
        }
        
        state["final_report"] = final_report
        
        print(f"\n[Orchestrator] Review completed in {final_report['metrics']['duration_seconds']:.2f}s")
        
        return state
    
    def review_paper(self, arxiv_id: str) -> Dict[str, Any]:
        """Review a paper given its arXiv ID."""
        print(f"\n{'='*60}")
        print(f"Starting multi-agent review for paper: {arxiv_id}")
        print(f"{'='*60}")
        
        # Initialize state with empty dicts for new agents
        initial_state: ReviewState = {
            "arxiv_id": arxiv_id,
            "reader_output": {},
            "meta_reviewer_output": {},
            "critic_output": {},
            "cite_output": {},
            "publication_output": {},  # <--- NEW
            
            "final_report": {},
            "error": "",
            "start_time": time.time(),
            "end_time": 0
        }
        
        final_state = self.workflow.invoke(initial_state)
        return final_state["final_report"]


def main():
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="Multi-Agent Paper Reviewer")
    parser.add_argument("--arxiv-id", type=str, required=True, help="arXiv paper ID")
    parser.add_argument("--output", type=str, default="review_output.json", help="Output file")
    
    args = parser.parse_args()
    orchestrator = PaperReviewOrchestrator()
    result = orchestrator.review_paper(args.arxiv_id)
    
    with open(args.output, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\nReview saved to: {args.output}")

if __name__ == "__main__":
    main()