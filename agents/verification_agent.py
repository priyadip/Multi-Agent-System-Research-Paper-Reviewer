"""
VerificationAgent - checks that the stored understanding is faithful and complete.

Acts as an LLM judge: given the per-part notes the understanding was built from and
the synthesized global understanding, it checks coverage (are all parts represented?)
and faithfulness (any claims not supported by the notes?), and returns a score plus
any gaps.
"""

import re
from typing import Dict, Any, List
from .base_agent import BaseAgent


class VerificationAgent(BaseAgent):
    """Verifies the understanding faithfully and completely covers the paper."""

    def __init__(self, api_key: str = None, model: str = None):
        super().__init__(
            name="VerificationAgent",
            role="Verify that a paper's stored understanding is complete and faithful",
            api_key=api_key,
            model=model
        )

    def verify(self, part_notes: List[str], global_understanding: str,
               title: str = "") -> Dict[str, Any]:
        """Judge coverage and faithfulness of the understanding vs the source notes."""
        self.tool_calls_count = 0
        self.tool_calls_count += 1

        notes = "\n\n".join(f"[Part {i}]\n{n}" for i, n in enumerate(part_notes, 1))

        resp = self.call_llm([
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": f"""You are verifying a "global understanding" of the paper "{title}".
It was synthesized from the per-part notes below. Check two things:

1. COVERAGE — is every part/topic from the notes represented in the understanding?
2. FAITHFULNESS — does the understanding contain any claim NOT supported by the notes?

PER-PART NOTES (the source of truth):
{notes}

GLOBAL UNDERSTANDING (to verify):
{global_understanding}

Respond in EXACTLY this format:
SCORE: <integer 0-100 for how completely & faithfully it covers the paper>
GAPS: <bullet list of missing topics or unsupported claims, or "none">
VERDICT: <one sentence overall judgement>"""}
        ], temperature=0.2)

        score = None
        m = re.search(r"SCORE:\s*(\d{1,3})", resp)
        if m:
            score = min(100, int(m.group(1)))

        return {"report": resp, "score": score}

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Standard entry point (satisfies BaseAgent)."""
        result = self.verify(
            input_data.get("part_notes", []),
            input_data.get("global_understanding", ""),
            input_data.get("title", "")
        )
        return self.format_output(result)
