"""
Critic Agent - Identifies strengths and weaknesses.
"""

from typing import Dict, Any, List
from .base_agent import BaseAgent


class CriticAgent(BaseAgent):
    """Agent responsible for critical evaluation of papers."""
    
    def __init__(self, api_key: str = None):
        super().__init__(
            name="CriticAgent",
            role="Identify strengths, weaknesses, and provide constructive criticism",
            api_key=api_key
        )
    
    def identify_strengths(self, paper_info: Dict[str, Any], meta_review: Dict[str, Any]) -> List[str]:
        """
        Identify paper strengths.
        
        Args:
            paper_info: Paper information
            meta_review: Meta-review results
            
        Returns:
            List of strengths
        """
        self.tool_calls_count += 1
        
        abstract = paper_info.get("metadata", {}).get("abstract", "")
        overall_review = meta_review.get("output", {}).get("overall_review", "")
        
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": f"""Based on this paper and meta-review, identify 3-5 key strengths:

Abstract: {abstract}

Meta-Review: {overall_review}

List specific strengths that would help students understand what makes this paper valuable.
Format as a numbered list."""}
        ]
        
        response = self.call_llm(messages, temperature=0.6)
        
        # Parse response into list
        strengths = [s.strip() for s in response.split('\n') if s.strip() and any(c.isdigit() for c in s[:3])]
        
        return strengths if strengths else [response]
    
    def identify_weaknesses(self, paper_info: Dict[str, Any], meta_review: Dict[str, Any]) -> List[str]:
        """
        Identify paper weaknesses and limitations.
        
        Args:
            paper_info: Paper information
            meta_review: Meta-review results
            
        Returns:
            List of weaknesses
        """
        self.tool_calls_count += 1
        
        abstract = paper_info.get("metadata", {}).get("abstract", "")
        title = paper_info.get("paper_title", "")
        
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": f"""Critically analyze this paper and identify 3-5 weaknesses or limitations:

Title: {title}
Abstract: {abstract}

Consider:
- Methodological limitations
- Scope constraints
- Assumptions made
- Missing comparisons
- Generalizability issues

Format as a numbered list. Be constructive and specific."""}
        ]
        
        response = self.call_llm(messages, temperature=0.6)
        
        # Parse response into list
        weaknesses = [w.strip() for w in response.split('\n') if w.strip() and any(c.isdigit() for c in w[:3])]
        
        return weaknesses if weaknesses else [response]
    
    def suggest_improvements(self, weaknesses: List[str]) -> str:
        """
        Suggest improvements based on identified weaknesses.
        
        Args:
            weaknesses: List of weaknesses
            
        Returns:
            Improvement suggestions
        """
        self.tool_calls_count += 1
        
        weaknesses_text = "\n".join(weaknesses)
        
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": f"""Based on these weaknesses, suggest constructive improvements:

Weaknesses:
{weaknesses_text}

Provide 3-4 specific, actionable suggestions for how future work could address these issues.
Keep it brief and student-friendly."""}
        ]
        
        response = self.call_llm(messages, temperature=0.7)
        
        return response
    
    def generate_critique_summary(self, strengths: List[str], weaknesses: List[str], 
                                  improvements: str) -> str:
        """
        Generate overall critique summary.
        
        Args:
            strengths: List of strengths
            weaknesses: List of weaknesses
            improvements: Improvement suggestions
            
        Returns:
            Critique summary
        """
        return f"""
### Critical Analysis

**Key Strengths:**
{chr(10).join(strengths)}

**Limitations and Weaknesses:**
{chr(10).join(weaknesses)}

**Suggested Improvements:**
{improvements}
"""
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process paper and provide critical analysis.
        """
        self.tool_calls_count = 0  # Reset so counts don't accumulate across papers
        # --- FIX 1: UNWRAP THE READER OUTPUT ---
        # We need to add .get("output", {}) to get to the actual data
        paper_info = input_data.get("reader_output", {}).get("output", {})
        
        # Meta review is handled differently in your code (it expects the wrapper), 
        # so we leave this as is or unwrap it if your meta-reviewer acts like the reader.
        # Assuming meta-reviewer returns standard format:
        meta_review = input_data.get("meta_reviewer_output", {})
        
        # Identify strengths and weaknesses
        strengths = self.identify_strengths(paper_info, meta_review)
        weaknesses = self.identify_weaknesses(paper_info, meta_review)
        
        # Suggest improvements
        improvements = self.suggest_improvements(weaknesses)
        
        # Generate summary
        critique_summary = self.generate_critique_summary(strengths, weaknesses, improvements)
        
        result = {
            "status": "success",
            "strengths": strengths,
            "weaknesses": weaknesses,
            "improvements": improvements,
            "critique_summary": critique_summary,
            # --- FIX 2: UPDATE TITLE ACCESS ---
            # Since paper_info is now unwrapped, we access paper_title directly
            "paper_title": paper_info.get("paper_title", "Unknown")
        }
        
        return self.format_output(result)