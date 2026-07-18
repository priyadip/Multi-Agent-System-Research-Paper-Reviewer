"""
Publication Agent - (Robust Hybrid Strategy)
Finds publication details by checking:
1. arXiv Metadata (Internal)
2. PDF Text Scan (Internal)
3. Google Scholar / Smart Web Search (External Fallback)
"""

from typing import Dict, Any, Optional
import re
from .base_agent import BaseAgent

class PublicationAgent(BaseAgent):
    """
    Agent responsible for finding publication venue by checking
    internal metadata and PDF text first, then falling back to smart search.
    """
    
    def __init__(self, api_key: str = None, model: str = None):
        super().__init__(
            name="PublicationAgent",
            role="Identify authoritative publication details from metadata and PDF text.",
            api_key=api_key,
            model=model
        )

    def _parse_year(self, text: str) -> Optional[str]:
        """Utility to find a year (e.g., 2024) in a string."""
        match = re.search(r"(20\d{2})", text)
        return match.group(1) if match else None

    # --- Step 1: Check Internal Metadata [BYPASSED] ---
    def _check_arxiv_metadata(self, metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Checks the arXiv metadata (journal_ref).
        This is the most reliable, author-provided source.
        """
        self.tool_calls_count += 1
        print("   [PubAgent] Step 1: Checking arXiv metadata (journal_ref)... [SKIPPED]")
        # Bypassed
        return None

    # --- Step 2: Scan PDF Text [BYPASSED] ---
    def _scan_pdf_text(self, full_text: str) -> Optional[Dict[str, Any]]:
        """
        Scans the PDF text (header/footer) for publication notes.
        This is fast and requires no network.
        """
        self.tool_calls_count += 1
        print("   [PubAgent] Step 2: Scanning PDF text for venue keywords... [SKIPPED]")
        # Bypassed
        return None

    # --- Step 3: Smart Web Search (Fallback) [BYPASSED] ---
    def _fallback_smart_search(self, title: str) -> Optional[Dict[str, Any]]:
        """
        If all else fails, do targeted web searches.
        """
        self.tool_calls_count += 1
        print("   [PubAgent] Step 3: Falling back to Smart Web Search... [SKIPPED]")
        # Bypassed
        return None

    # --- Main Process [MODIFIED] ---
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        [MODIFIED] This agent is currently paused and will return a 
        placeholder message instead of processing.
        """
        self.tool_calls_count = 0  # Reset so counts don't accumulate across papers

        # This is the message you requested
        pause_message = "(Unavailable due to API limits)"

        print(f"\n [PubAgent] PAUSED: {pause_message}")

        # --- Final Consolidation ---
        # Return the placeholder message as the main output
        final_result = {
            "publication_status": "Paused",
            "venue": pause_message,
            "link": None,
            "publication_date": None,
            "source": "Agent Paused",
            "web_search_evidence": pause_message
        }

        return self.format_output(final_result)