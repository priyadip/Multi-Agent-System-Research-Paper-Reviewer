"""
Learning Agent - Explains a paper's concepts and mathematics for learners.

Used on-demand from the UI's "Learn" tab (not part of the main review pipeline).
Produces an undergraduate-level breakdown of the paper and answers follow-up
questions grounded in the paper text.
"""

from typing import Dict, Any, List, Tuple
from .base_agent import BaseAgent


class LearningAgent(BaseAgent):
    """Agent that teaches the paper: concepts, intuition, and math."""

    def __init__(self, api_key: str = None, model: str = None):
        super().__init__(
            name="LearningAgent",
            role="Explain a research paper's concepts and mathematics so an "
                 "undergraduate can understand them",
            api_key=api_key,
            model=model
        )

    def explain_paper(self, full_text: str, title: str = "") -> str:
        """
        Generate a structured, undergraduate-level explanation of the paper,
        including its main equations rendered in LaTeX.
        """
        self.tool_calls_count += 1

        # Bound the context to control tokens / rate limits.
        excerpt = (full_text or "")[:16000]

        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": f"""You are a friendly tutor explaining a research paper to an undergraduate
student who knows basic calculus, linear algebra, and introductory machine
learning, but is NOT an expert in this specific area.

Explain the paper below in clear, structured Markdown with these sections:

## Core Idea
2-3 sentences: what problem it solves and the key idea, in plain language.

## Background You Need
The prerequisite concepts required to follow the paper (brief).

## Key Concepts
The main ideas, each explained with intuition and a simple analogy where helpful.

## The Math, Explained
Identify the paper's main equations / formulas / methods and explain each one:
- what it computes,
- what every symbol means,
- the intuition for *why* it is written that way.
Render all mathematics as LaTeX: inline as $...$ and display equations as $$...$$.
If the extracted text garbled an equation, reconstruct it from your knowledge of
the paper and note that you did so.

## Why It Works
The key insight that makes the approach effective.

## Takeaways
3-4 bullet points a student should remember.

Paper title: {title}

Paper text (may be truncated / imperfectly extracted from PDF):
\"\"\"
{excerpt}
\"\"\""""}
        ]

        return self.call_llm(messages, temperature=0.4)

    def answer_question(self, full_text: str, title: str, question: str,
                        history: List[Tuple[str, str]] = None) -> str:
        """
        Answer a learner's question about the paper, grounded in the paper text,
        at an undergraduate level with LaTeX for any math.
        """
        self.tool_calls_count += 1

        excerpt = (full_text or "")[:10000]

        messages = [
            {"role": "system", "content": f"""You are a friendly tutor helping an undergraduate understand this research
paper. Answer questions clearly with intuition and analogies. Render any
mathematics as LaTeX (inline $...$, display $$...$$). Ground your answers in the
paper; if it doesn't cover something, use your general knowledge and say so.

Paper title: {title}

Paper excerpt (may be truncated / imperfectly extracted):
\"\"\"
{excerpt}
\"\"\""""}
        ]

        # Include recent conversation for context (skip the message being answered).
        for role, content in (history or [])[-6:]:
            if role in ("user", "assistant"):
                messages.append({"role": role, "content": content})

        messages.append({"role": "user", "content": question})

        return self.call_llm(messages, temperature=0.5)

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Standard entry point (satisfies BaseAgent); returns an explanation."""
        self.tool_calls_count = 0
        paper_info = input_data.get("reader_output", {}).get("output", input_data)
        full_text = paper_info.get("full_text", "") or \
            paper_info.get("metadata", {}).get("abstract", "")
        title = paper_info.get("paper_title", "")
        explanation = self.explain_paper(full_text, title)
        return self.format_output({"status": "success", "explanation": explanation})
