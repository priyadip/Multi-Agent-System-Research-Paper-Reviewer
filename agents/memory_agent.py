"""
MemoryAgent - maintains a running memory of a learning conversation.

Problem it solves: passing only the last few chat turns to the LLM means older
context is forgotten in a long session. This agent keeps a compact but COMPLETE
running memory — every important fact, definition, and equation discussed so far —
which is fed back into each answer. So the tutor never forgets earlier learning.

The memory is a rolling summary: recent turns stay verbatim in the chat, older
context is compressed here (not dropped), so it stays within the token budget.
"""

from typing import Dict, Any
from .base_agent import BaseAgent
from .learning_agent import MATH_FORMATTING_RULES


class MemoryAgent(BaseAgent):
    """Keeps a running memory of what the learner has covered."""

    def __init__(self, api_key: str = None, model: str = None):
        super().__init__(
            name="MemoryAgent",
            role="Maintain a complete running memory of the learning conversation "
                 "so nothing discussed is ever forgotten",
            api_key=api_key,
            model=model
        )

    def update(self, current_memory: str, question: str, answer: str,
               title: str = "") -> str:
        """Fold the latest Q&A exchange into the running memory (nothing dropped)."""
        self.tool_calls_count += 1

        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": f"""You maintain a running MEMORY of a learning conversation about the paper "{title}".
Update the memory to incorporate the latest exchange. Keep it concise (compact
bullet notes) but COMPLETE — preserve ALL important facts, definitions, equations,
symbols, and clarifications the learner has covered so far. Never drop earlier
points; merge related ones. Keep any math as LaTeX.

{MATH_FORMATTING_RULES}

CURRENT MEMORY:
{current_memory or '(empty — this is the first exchange)'}

LATEST EXCHANGE:
Q: {question}
A: {answer}

Return ONLY the updated memory as bullet notes."""}
        ]

        return self.call_llm(messages, temperature=0.2)

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Standard entry point (satisfies BaseAgent)."""
        memory = self.update(
            input_data.get("current_memory", ""),
            input_data.get("question", ""),
            input_data.get("answer", ""),
            input_data.get("title", "")
        )
        return self.format_output({"status": "success", "memory": memory})
