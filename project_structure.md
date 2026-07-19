# Architecture & Project Structure

A multi-agent system for reviewing and learning academic papers from arXiv, built
with **LangGraph** orchestration and **Groq** LLMs, exposed through a **Streamlit** UI.

> For setup and usage instructions, see [README.md](README.md). This document
> focuses on the architecture and code layout.

---

## Two Subsystems

### 1. Review Pipeline (LangGraph, sequential)

Runs when a user submits an arXiv ID. Orchestrated as a linear LangGraph workflow.

```
arXiv ID
   │
   ▼
┌──────────┐   ┌─────────────┐   ┌──────────────┐   ┌────────┐   ┌────────┐   ┌──────────┐
│ Reader   │──▶│ Publication │──▶│ MetaReviewer │──▶│ Critic │──▶│  Cite  │──▶│ Finalize │
│ (arXiv + │   │  (paused,   │   │ (methodology │   │(str/wk)│   │(refs + │   │ (compile │
│  PDF)    │   │ placeholder)│   │  + contrib)  │   │        │   │in-text)│   │  report) │
└──────────┘   └─────────────┘   └──────────────┘   └────────┘   └────────┘   └──────────┘
```

- **Reader** — fetches arXiv metadata, downloads the PDF, extracts full text.
- **Publication** — placeholder (venue detection paused); kept so the graph stays intact.
- **MetaReviewer** — methodology + contribution assessment, overall review.
- **Critic** — strengths, weaknesses, suggested improvements.
- **Cite** — counts bibliography references and lists in-text citations with context.
- **Finalize** — compiles everything into one JSON report.

### 2. Learn Subsystem (multi-agent RAG, on-demand)

Runs from the UI's **🎓 Learn** tab, on the extracted full text. Not part of the
LangGraph pipeline — it is triggered by the user and covers the *whole* paper.

```
Full paper text
   │
   ├───────────────▶ PaperRAG ── chunks whole paper ── semantic embedding index
   │                                                    (TF-IDF fallback)
   ▼
┌──────────────────┐     ┌──────────────────┐
│ UnderstandingAgent│──▶ │ VerificationAgent │
│  map: summarize   │     │  LLM judge:      │
│  each part        │     │  coverage +      │
│  reduce: connect  │     │  faithfulness    │
│  into 1 explanation│    │  → score + gaps  │
└──────────────────┘     └──────────────────┘
                                 │
   follow-up question ───────────┤
   │                             ▼
   └──▶ PaperRAG.retrieve ──▶ LearningAgent (Tutor)
        (top-k chunks from      answers grounded in retrieved
         the whole paper)       chunks + verified understanding
```

---

## Project Structure

```
Multi-Agent-System-Research-Paper-Reviewer/
├── agents/
│   ├── __init__.py
│   ├── base_agent.py            # Base class: Groq client, call_llm (+ retry/backoff)
│   ├── reader_agent.py          # arXiv metadata + PDF text extraction
│   ├── meta_reviewer_agent.py   # Methodology & contribution assessment
│   ├── critic_agent.py          # Strengths, weaknesses, improvements
│   ├── cite_agent.py            # Reference count + in-text citation context
│   ├── publication_agent.py     # Venue detection (paused placeholder)
│   ├── orchestrator.py          # LangGraph review workflow
│   ├── learning_agent.py        # Tutor: undergrad explanations + RAG Q&A
│   ├── understanding_agent.py   # Whole-paper comprehension (map-reduce)
│   ├── verification_agent.py    # Coverage/faithfulness judge
│   ├── memory_agent.py          # Running conversation memory (never forget)
│   ├── rag_store.py             # PaperRAG: chunk + embed + retrieve
│   └── llm_pool.py              # Multi-provider round-robin + failover
├── ui/
│   └── app.py                   # Streamlit UI (review + Learn tab)
├── eval/
│   ├── test_cases.json          # Evaluation test cases
│   ├── run_eval.py              # Evaluation harness
│   └── metrics.py               # Metrics computation
├── mcp-server/
│   └── server.py                # Model Context Protocol (MCP) server
├── example_usage.py             # CLI demo / batch processing
├── requirements.txt             # Pinned dependencies
├── README.md
└── project_structure.md         # (this file)
```

---

## Key Design Points

- **Bring-your-own key(s) & model** — every agent takes an `api_key`/`model`, or a
  shared `llm_pool`. The Streamlit app passes per-session keys; nothing is stored.
  Falls back to `GROQ_API_KEY` / `MODEL_NAME` env vars for local/CLI use.
- **Multi-provider pool** (`llm_pool.py`) — Groq, Gemini, Cerebras, and OpenRouter
  are all OpenAI-compatible, so one client (per-provider base URL) round-robins
  across whatever keys the user supplies, failing over on rate limits. When a pool
  is set on an agent, `call_llm` routes through it.
- **Never-forget memory** (`memory_agent.py`) — the Learn Q&A keeps a running,
  compressed memory of the whole conversation so earlier context is never dropped.
- **Rate-limit handling** — `base_agent.call_llm` retries with exponential backoff
  on Groq `429` errors (important for the Learn pipeline's multiple calls).
- **RAG without an embeddings API** — Groq serves no embedding model, so `PaperRAG`
  uses `sentence-transformers` locally when available and **falls back to lexical
  TF-IDF** otherwise, so the app never breaks.
- **KaTeX-safe math** — Learn-tab prompts enforce `$…$` / `$$…$$` and `aligned`
  environments; the UI post-processes LaTeX so equations render reliably.
- **One paper at a time**, internet required (arXiv + Groq).

---

## Testing

```bash
python eval/run_eval.py
```

Runs the test cases and reports success rate, latency, and tool-call counts.

---

## Author

**Priyadip Sau** — [website](https://priyadipsau.in/) · saupriyadip571@gmail.com
