"""
UnderstandingAgent - builds a full, connected understanding of the whole paper.

Uses map-reduce: summarize each part of the paper (map), then synthesize a single
coherent, undergraduate-level explanation that connects all parts (reduce). Because
it processes the whole paper part-by-part, it covers content beyond the first pages
(unlike naive prompt-truncation).
"""

import re
from typing import Dict, Any, List
from .base_agent import BaseAgent
from .learning_agent import MATH_FORMATTING_RULES


class UnderstandingAgent(BaseAgent):
    """Comprehends the entire paper and produces a connected understanding."""

    def __init__(self, api_key: str = None, model: str = None):
        super().__init__(
            name="UnderstandingAgent",
            role="Build a complete, connected, undergraduate-level understanding of "
                 "the entire paper",
            api_key=api_key,
            model=model
        )

    @staticmethod
    def _segments(text: str, n_segments: int = 6) -> List[str]:
        """Split the whole paper into roughly equal parts (covers all pages)."""
        text = re.sub(r"\s+", " ", text or "").strip()
        if not text:
            return []
        seg_len = max(1, len(text) // n_segments)
        segs = [text[i:i + seg_len] for i in range(0, len(text), seg_len)]
        return segs[:n_segments + 1]

    def summarize_parts(self, full_text: str, title: str) -> List[str]:
        """MAP: summarize each part of the paper into structured notes."""
        segments = [s for s in self._segments(full_text) if s.strip()]
        total = len(segments)
        print(f"[UnderstandingAgent] Reading paper in {total} parts...", flush=True)
        notes = []
        for i, seg in enumerate(segments, 1):
            self.tool_calls_count += 1
            print(f"[UnderstandingAgent] Summarizing part {i}/{total}...", flush=True)
            resp = self.call_llm([
                {"role": "system", "content": self.get_system_prompt()},
                {"role": "user", "content": f"""This is part {i} of {len(segments)} of the paper "{title}".
Summarize it into concise bullet notes capturing: key claims, methods, definitions,
important equations (keep math as LaTeX $...$), and results found in THIS part only.

Part {i}:
\"\"\"
{seg}
\"\"\""""}
            ], temperature=0.3)
            notes.append(resp)
        return notes

    def synthesize(self, part_notes: List[str], title: str) -> str:
        """REDUCE: connect all part-notes into one undergraduate-level explanation."""
        self.tool_calls_count += 1
        print("[UnderstandingAgent] Synthesizing the full understanding...", flush=True)
        joined = "\n\n".join(f"[Part {i}]\n{n}" for i, n in enumerate(part_notes, 1))
        return self.call_llm([
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": f"""You have per-part notes covering the ENTIRE paper "{title}".
Synthesize them into ONE coherent, undergraduate-level explanation in Markdown that
connects all parts. Use these sections:

## Core Idea
## Background You Need
## Key Concepts
## The Math, Explained   (main equations, each symbol defined, with intuition)
## How It All Connects   (how the parts/sections fit together end-to-end)
## Results & Takeaways

{MATH_FORMATTING_RULES}

Per-part notes:
{joined}"""}
        ], temperature=0.35)

    def build_understanding(self, full_text: str, title: str = "") -> Dict[str, Any]:
        """Run the full map-reduce comprehension over the whole paper."""
        self.tool_calls_count = 0
        part_notes = self.summarize_parts(full_text, title)
        if not part_notes:
            return {"part_notes": [], "global_understanding": "",
                    "status": "no_text"}
        global_understanding = self.synthesize(part_notes, title)
        return {
            "part_notes": part_notes,
            "global_understanding": global_understanding,
            "status": "success"
        }

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Standard entry point (satisfies BaseAgent)."""
        paper_info = input_data.get("reader_output", {}).get("output", input_data)
        full_text = paper_info.get("full_text", "") or \
            paper_info.get("metadata", {}).get("abstract", "")
        title = paper_info.get("paper_title", "")
        result = self.build_understanding(full_text, title)
        return self.format_output(result)
