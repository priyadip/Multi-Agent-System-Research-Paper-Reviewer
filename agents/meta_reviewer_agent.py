"""
Meta-Reviewer Agent - Provides comprehensive quality analysis.
"""

from typing import Dict, Any
from .base_agent import BaseAgent


class MetaReviewerAgent(BaseAgent):
    """Agent responsible for comprehensive paper analysis."""
    
    def __init__(self, api_key: str = None):
        super().__init__(
            name="MetaReviewerAgent",
            role="Provide comprehensive quality analysis and scoring",
            api_key=api_key
        )
    
    def analyze_methodology(self, paper_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze paper methodology.
        
        Args:
            paper_info: Paper information from reader agent
            
        Returns:
            Methodology analysis
        """
        self.tool_calls_count += 1
        
        abstract = paper_info.get("metadata", {}).get("abstract", "")
        title = paper_info.get("paper_title", "")
        
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": f"""As a meta-reviewer, analyze this paper's methodology:

Title: {title}
Abstract: {abstract}

Evaluate:
1. Research approach soundness
2. Clarity of methods
3. Reproducibility potential
4. Innovation level

Provide scores (1-10) and brief justifications for each aspect."""}
        ]
        
        response = self.call_llm(messages, temperature=0.5)
        
        return {
            "methodology_analysis": response
        }
    
    def evaluate_contribution(self, paper_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate paper's contribution to the field.
        
        Args:
            paper_info: Paper information
            
        Returns:
            Contribution evaluation
        """
        self.tool_calls_count += 1
        
        abstract = paper_info.get("metadata", {}).get("abstract", "")
        categories = paper_info.get("categories", [])
        
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": f"""Evaluate this paper's contribution:

Abstract: {abstract}
Categories: {', '.join(categories)}

Assess:
1. Novelty of approach
2. Impact potential
3. Relevance to field
4. Practical applicability

Provide an overall contribution score (1-10) with explanation."""}
        ]
        
        response = self.call_llm(messages, temperature=0.5)
        
        return {
            "contribution_evaluation": response
        }
    
    def generate_overall_review(self, methodology: Dict, contribution: Dict) -> str:
        """
        Generate overall meta-review.
        
        Args:
            methodology: Methodology analysis
            contribution: Contribution evaluation
            
        Returns:
            Overall review text
        """
        self.tool_calls_count += 1
        
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": f"""Synthesize these analyses into a meta-review:

Methodology Analysis:
{methodology.get('methodology_analysis', '')}

Contribution Evaluation:
{contribution.get('contribution_evaluation', '')}

Provide:
1. Overall assessment (2-3 sentences)
2. Key strengths (2-3 points)
3. Key areas for improvement (2-3 points)
4. Overall recommendation for students studying this paper
5. Final score (1-10)

Keep it clear and student-friendly."""}
        ]
        
        response = self.call_llm(messages, temperature=0.6)
        
        return response
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process paper and provide meta-review.
        
        Args:
            input_data: Dictionary containing paper information from reader agent
            
        Returns:
            Meta-review results
        """
        self.tool_calls_count = 0  # Reset so counts don't accumulate across papers
        # Analyze different aspects
        methodology = self.analyze_methodology(input_data)
        contribution = self.evaluate_contribution(input_data)
        
        # Generate overall review
        overall_review = self.generate_overall_review(methodology, contribution)
        
        result = {
            "status": "success",
            "methodology_analysis": methodology,
            "contribution_evaluation": contribution,
            "overall_review": overall_review,
            "paper_title": input_data.get("paper_title", "Unknown")
        }
        
        return self.format_output(result)