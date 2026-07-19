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

- **Reader**: fetches arXiv metadata, downloads the PDF, extracts full text.
- **Publication**: placeholder (venue detection paused); kept so the graph stays intact.
- **MetaReviewer**: methodology + contribution assessment, overall review.
- **Critic**: strengths, weaknesses, suggested improvements.
- **Cite**: counts bibliography references and lists in-text citations with context.
- **Finalize**: compiles everything into one JSON report.

Each node times itself and records `{agent, tool_calls, duration}`; the final report
exposes these under `metrics.per_agent`, which the evaluation harness uses to compute
real per-agent efficiency (no hardcoded figures).

### 2. Learn Subsystem (multi-agent RAG, on-demand)

Runs from the UI's **🎓 Learn** tab, on the extracted full text. Not part of the
LangGraph pipeline; it is triggered by the user and covers the *whole* paper.

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
│   ├── orchestrator.py          # LangGraph review workflow (+ per-agent metrics)
│   ├── learning_agent.py        # Tutor: undergrad explanations + RAG Q&A
│   ├── understanding_agent.py   # Whole-paper comprehension (map-reduce)
│   ├── verification_agent.py    # Coverage/faithfulness judge
│   ├── memory_agent.py          # Running conversation memory (never forget)
│   ├── rag_store.py             # PaperRAG: chunk + embed + retrieve
│   └── llm_pool.py              # Multi-provider round-robin + failover
├── ui/
│   └── app.py                   # Streamlit UI (review + Learn tab)
├── eval/
│   ├── test_cases.json          # Test suite (real arXiv IDs + error cases)
│   ├── run_eval.py              # Harness: run suite, check constraints + content
│   └── metrics.py               # Success rate, latency, per-agent efficiency
├── mcp-server/
│   └── server.py                # Model Context Protocol (MCP) server
├── example_usage.py             # CLI demo / batch processing
├── requirements.txt             # Pinned dependencies
├── README.md
└── project_structure.md         # (this file)
```

---

## Key Design Points

- **Bring-your-own key(s) & model**: every agent takes an `api_key`/`model`, or a
  shared `llm_pool`. The Streamlit app passes per-session keys; nothing is stored.
  Falls back to `GROQ_API_KEY` / `MODEL_NAME` env vars for local/CLI use.
- **Multi-provider pool** (`llm_pool.py`): Groq and NVIDIA (both OpenAI-compatible).
  Each task gets its own pool (see `build_task_pools` in `ui/app.py`): Review/Q&A/Memory
  on Groq; Understanding on NVIDIA `deepseek-v4-pro` (key 1); Verification on NVIDIA
  `deepseek-v4-flash` (key 2). Accuracy pools set `attempts_per_provider=8`; the pool
  retries the primary (NVIDIA) with exponential backoff on transient errors
  (`503`/`404`/`429`/timeout; only `401/402/403` are permanent → circuit breaker) before
  falling back to Groq. Calls are strictly sequential. When a pool is set on an agent,
  `call_llm` routes through it.
- **Never-forget memory** (`memory_agent.py`): the Learn Q&A keeps a running,
  compressed memory of the whole conversation so earlier context is never dropped.
- **Rate-limit handling**: `base_agent.call_llm` retries with exponential backoff
  on Groq `429` errors (important for the Learn pipeline's multiple calls).
- **RAG without an embeddings API**: Groq serves no embedding model, so `PaperRAG`
  uses `sentence-transformers` locally when available and **falls back to lexical
  TF-IDF** otherwise, so the app never breaks.
- **KaTeX-safe math**: Learn-tab prompts enforce `$…$` / `$$…$$` and `aligned`
  environments; the UI post-processes LaTeX so equations render reliably.
- **One paper at a time**, internet required (arXiv + Groq).

---

## Evaluation

```bash
python eval/run_eval.py --output eval/eval_results.json
```

The harness (`eval/run_eval.py`) loads a declarative test suite (`eval/test_cases.json`),
runs each case through the full pipeline, and checks the result. **A case passes only if
the observed status matches the expected one *and* no constraint is violated:**

- **Constraints per case**: `max_duration_seconds`, `min_tool_calls`, `max_tool_calls`,
  and `required_fields` (report keys that must be present).
- **Content check**: a structurally-"successful" review whose text is just LLM error
  strings (invalid key, rate-limit, etc.) is flagged via `_llm_error_markers` and fails.
  This is what makes the success rate trustworthy: a broken-key run is reported as failing,
  not as 100% passing.

`eval/metrics.py` (`MetricsCalculator`) is the single source of truth for metrics:
success rate, a latency distribution (mean/median/std/min/max/p95/p99), tool-call stats,
constraint violations by type, and a **per-agent efficiency profile** computed from
`report["metrics"]["per_agent"]`. Output is JSON-safe (plain floats) and the saved results
strip the paper's bulky `full_text`.

**Test suite**: real, well-known arXiv IDs for the success cases (GPT-3 `2005.14165`,
ViT `2010.11929`, Adam `1412.6980`, GANs `1406.2661`, Attention `1706.03762`) plus three
negative cases: an obviously invalid ID, an empty ID, and a **deliberately fake but
real-looking ID** (`2402.99999`) that verifies the pipeline flags a nonexistent paper
instead of hallucinating a review.

**Latest measured run** (live Groq free tier): 100% pass (8/8), 0 violations, 14 tool
calls/review, ~91 s mean latency/review (dominated by free-tier rate-limit backoff).

---

## Author

**Priyadip Sau** · [website](https://priyadipsau.in/) · saupriyadip571@gmail.com
