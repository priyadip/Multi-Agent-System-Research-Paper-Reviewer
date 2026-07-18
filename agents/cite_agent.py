"""
Cite Agent - Analyzes citations and references.
"""

from typing import Dict, Any, List
import re
from .base_agent import BaseAgent


class CiteAgent(BaseAgent):
    """Agent responsible for citation and reference analysis."""
    
    def __init__(self, api_key: str = None, model: str = None):
        super().__init__(
            name="CiteAgent",
            role="Analyze citations, references, and paper impact",
            api_key=api_key,
            model=model
        )
    
    def extract_potential_citations(self, abstract: str) -> List[str]:
        """
        Extract potential citation patterns from abstract.
        
        Args:
            abstract: Paper abstract
            
        Returns:
            List of citation patterns found
        """
        self.tool_calls_count += 1
        
        # Look for common citation patterns
        citation_patterns = [
            r'\[[\d,\s-]+\]',  # [1], [1,2], [1-3]
            r'\([A-Z][a-z]+\s+et\s+al\.,?\s+\d{4}\)',  # (Smith et al., 2020)
            r'\([A-Z][a-z]+\s+and\s+[A-Z][a-z]+,?\s+\d{4}\)',  # (Smith and Jones, 2020)
        ]
        
        citations = []
        for pattern in citation_patterns:
            matches = re.findall(pattern, abstract)
            citations.extend(matches)

        return citations

    # Shared citation-marker patterns (used for both counting and context)
    CITATION_PATTERNS = [
        r'\[[\d,\s-]+\]',                              # [1], [1,2], [1-3]
        r'\([A-Z][a-z]+\s+et\s+al\.,?\s+\d{4}\)',      # (Smith et al., 2020)
        r'\([A-Z][a-z]+\s+and\s+[A-Z][a-z]+,?\s+\d{4}\)',  # (Smith and Jones, 2020)
    ]

    def extract_in_text_citations(self, text: str, window: int = 160,
                                  max_items: int = 60) -> List[Dict[str, str]]:
        """
        Find each unique in-text citation marker and capture the surrounding
        sentence so the reader can see what the citation supports.

        Args:
            text: Full paper text (or abstract fallback)
            window: Characters of context to keep on each side of the marker
            max_items: Cap on how many citations to return (avoids huge payloads)

        Returns:
            List of {"marker": ..., "context": ...} dicts, first-seen order
        """
        self.tool_calls_count += 1

        if not text:
            return []

        seen = {}
        for pattern in self.CITATION_PATTERNS:
            for m in re.finditer(pattern, text):
                marker = m.group(0).strip()
                if marker in seen:
                    continue
                start = max(0, m.start() - window)
                end = min(len(text), m.end() + window)
                # Collapse whitespace/newlines so the snippet reads as one line
                snippet = re.sub(r'\s+', ' ', text[start:end]).strip()
                seen[marker] = snippet
                if len(seen) >= max_items:
                    break

        return [{"marker": k, "context": v} for k, v in seen.items()]

    def count_references(self, full_text: str) -> Dict[str, Any]:
        """
        Count the actual entries in the paper's References / Bibliography
        section (the "total citations used"), not just inline markers.

        Args:
            full_text: Extracted PDF text

        Returns:
            Dict with total_references (int) and how it was detected
        """
        self.tool_calls_count += 1

        if not full_text:
            return {"total_references": 0, "method": "no_text"}

        lower = full_text.lower()

        # Locate the start of the reference list (use the LAST heading match,
        # since "references" can also appear earlier in the body).
        ref_start = -1
        for kw in ("references", "bibliography"):
            idx = lower.rfind("\n" + kw)
            if idx == -1:
                idx = lower.rfind(kw)
            ref_start = max(ref_start, idx)

        if ref_start == -1:
            return {"total_references": 0, "method": "no_references_section"}

        ref_section = full_text[ref_start:]

        # Strip tokens that contain year-like digits but are NOT publication
        # years: arXiv IDs (e.g. 2208.07339), URLs, and DOIs. Without this,
        # an arXiv id's "2208" or a stray year gets miscounted as a reference.
        cleaned = re.sub(r'arxiv:\s*\d{4}\.\d{4,5}(v\d+)?', ' ', ref_section, flags=re.I)
        cleaned = re.sub(r'https?://\S+', ' ', cleaned)
        cleaned = re.sub(r'doi:\s*\S+', ' ', cleaned, flags=re.I)

        # Style 1: numbered references bracketed at line start -> [1] [2] ... [40].
        # Count DISTINCT indices (not max(), which explodes on any stray number).
        bracketed = [int(n) for n in re.findall(r'(?m)^\s*\[(\d{1,3})\]', cleaned)]
        if len(bracketed) >= 3:
            total = len(set(bracketed))
            return self._sanity_check(total, "bracketed")

        # Style 2 (unnumbered / author-year): each entry ends with a publication
        # year followed by a period, e.g. "... Wasserstein gan, 2017." This is an
        # estimate — PDF text of author-year lists can't be counted exactly.
        entry_years = re.findall(r'(?<!\d)(?:19|20)\d{2}[a-z]?\.', cleaned)
        if entry_years:
            return self._sanity_check(len(entry_years), "author_year_estimate")

        return {"total_references": 0, "method": "unrecognized_format"}

    @staticmethod
    def _sanity_check(total: int, method: str) -> Dict[str, Any]:
        """Reject implausible counts so a parsing glitch can't surface a year."""
        if total <= 0 or total > 500:
            return {"total_references": 0, "method": f"{method}_implausible"}
        return {"total_references": total, "method": method}

    def analyze_citation_context(self, paper_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze citation context and importance.
        
        Args:
            paper_info: Paper information
            
        Returns:
            Citation context analysis
        """
        self.tool_calls_count += 1
        
        abstract = paper_info.get("metadata", {}).get("abstract", "")
        title = paper_info.get("paper_title", "")
        categories = paper_info.get("categories", [])
        
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": f"""Analyze the citation context for this paper:

Title: {title}
Categories: {', '.join(categories)}
Abstract: {abstract}

Provide:
1. Likely foundational papers this work builds upon (3-4 examples)
2. Related contemporary work (2-3 examples)
3. Potential impact areas for future citations
4. Citation network position (is it building on classics, or breaking new ground?)

Be specific but acknowledge these are educated inferences."""}
        ]
        
        response = self.call_llm(messages, temperature=0.6)
        
        return {
            "citation_context": response
        }
    
    def analyze_reference_quality(self, paper_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze the quality and breadth of references.
        
        Args:
            paper_info: Paper information
            
        Returns:
            Reference quality analysis
        """
        self.tool_calls_count += 1
        
        abstract = paper_info.get("metadata", {}).get("abstract", "")
        citations = self.extract_potential_citations(abstract)
        
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": f"""Based on this abstract, assess the reference quality:

Abstract: {abstract}
Citation markers found: {len(citations)}

Evaluate:
1. Breadth of literature coverage (based on topic scope)
2. Balance between classic and recent work
3. Interdisciplinary connections
4. Quality indicators

Provide a brief assessment suitable for students."""}
        ]
        
        response = self.call_llm(messages, temperature=0.6)
        
        return {
            "reference_quality": response,
            "citation_count_estimate": len(citations)
        }
    
    def generate_citation_recommendations(self, paper_info: Dict[str, Any]) -> str:
        """
        Generate recommendations for students following citation trails.
        
        Args:
            paper_info: Paper information
            
        Returns:
            Citation recommendations
        """
        self.tool_calls_count += 1
        
        title = paper_info.get("paper_title", "")
        categories = paper_info.get("categories", [])
        
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": f"""For students reading this paper:

Title: {title}
Categories: {', '.join(categories)}

Recommend:
1. Key papers to read before this one (2-3)
2. Papers to read after this one for deeper understanding (2-3)
3. How to use citations effectively when studying this topic
4. Warning about citation pitfalls in this area

Keep it practical and student-focused."""}
        ]
        
        response = self.call_llm(messages, temperature=0.7)
        
        return response
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process paper and provide citation analysis.
        
        Args:
            input_data: Dictionary containing paper information
            
        Returns:
            Citation analysis results
        """
        self.tool_calls_count = 0  # Reset so counts don't accumulate across papers
        paper_info = input_data.get("reader_output", {}).get("output", {})

        # Prefer full PDF text; fall back to "text", then to the abstract.
        full_text = paper_info.get("full_text") or paper_info.get("text") or ""
        text_to_analyze = full_text or paper_info.get("metadata", {}).get("abstract", "")

        # 1) TOTAL CITATIONS USED — count entries in the References section.
        ref_info = self.count_references(full_text)
        total_references = ref_info["total_references"]

        # 2) IN-TEXT CITATIONS — each unique marker with its surrounding context.
        in_text_citations = self.extract_in_text_citations(text_to_analyze)
        in_text_count = len(in_text_citations)

        # Analyze citation context
        citation_context = self.analyze_citation_context(paper_info)

        # Analyze reference quality
        reference_quality = self.analyze_reference_quality(paper_info)

        # Generate recommendations
        recommendations = self.generate_citation_recommendations(paper_info)

        result = {
            "status": "success",
            # "Total citations used" = actual reference-list entries
            "total_references": total_references,
            "reference_detection_method": ref_info["method"],
            # In-text citation markers, each with a context snippet
            "in_text_citations": in_text_citations,
            "in_text_citation_count": in_text_count,
            # Backward-compatible headline count: prefer the true reference
            # count, but fall back to inline markers if the ref list wasn't found.
            "citation_count": total_references if total_references else in_text_count,
            "citation_context": citation_context,
            "reference_quality": reference_quality,
            "recommendations": recommendations,
            "paper_title": paper_info.get("paper_title", "Unknown")
        }

        return self.format_output(result)