# Multi-Agent Research Paper Reviewer

> **Live demo:** https://multi-agent-system-research-paper-reviewer.streamlit.app/
> Paste your own free [Groq API key](https://console.groq.com/keys) in the sidebar to run a review. The key is used only for your session and is never stored.

An AI-powered multi-agent system for reviewing academic papers from arXiv. A team of specialized agents, orchestrated with **LangGraph** and powered by **Groq** LLMs, reads a paper and produces a structured review: a summary, a quality assessment, a critical analysis, and a citation breakdown.

## Features

- **Multi-agent architecture**: specialized agents for reading, meta-review, critique, and citation analysis, coordinated by a LangGraph workflow.
- **Two interfaces**: an interactive Streamlit web UI with live progress, plus command-line scripts.
- **In-depth analysis**: goes beyond summarization to surface strengths, weaknesses, and concrete suggestions for improvement.
- **Citation analysis**: counts references in the bibliography and lists in-text citations with the surrounding context.
- **Learn tab (multi-agent RAG)**: three agents read the *whole* paper: an **Understanding** agent comprehends and connects all sections (map-reduce), a **Verification** agent scores coverage/faithfulness, and a **Tutor** answers follow-up questions grounded in passages retrieved from the entire paper via semantic RAG (with a lexical TF-IDF fallback). Math renders as LaTeX.
- **Bring your own keys**: Groq runs the review & Q&A (fast); two optional NVIDIA keys run the accuracy-critical Learn steps on DeepSeek. Nothing is stored server-side.
- **Accuracy-first routing**: Understanding uses NVIDIA `deepseek-v4-pro` (key 1), Verification uses `deepseek-v4-flash` (key 2). These retry with exponential backoff on NVIDIA's transient `503`/`404`/`429` (up to ~8×, since NVIDIA's free tier is ~40 RPM and returns "workers busy") and only fall back to Groq if all retries fail, so a review favours correctness over speed and never hard-fails.
- **Automated evaluation**: an end-to-end harness runs a suite of arXiv papers through the full pipeline, checks each review against constraints (max duration, tool-call bounds, required fields) *and* a content sanity check (a "successful" review must not just be API-error text), and reports success rate, a latency distribution, tool-call stats, and a **real per-agent efficiency profile** measured from per-node timing. See [Evaluation](#evaluation).

## Agents

**Review pipeline** (LangGraph, runs on submit):

| Agent | Role |
|-------|------|
| **Reader** | Fetches arXiv metadata, downloads the PDF, and extracts content |
| **Meta-Reviewer** | Assesses methodology and contribution, produces an overall review |
| **Critic** | Identifies strengths, weaknesses, and suggested improvements |
| **Cite** | Counts references and analyzes in-text citations and their context |
| **Publication** | Placeholder for venue detection (currently paused) |

**Learn subsystem** (multi-agent RAG, on-demand in the 🎓 Learn tab):

| Agent | Role |
|-------|------|
| **Understanding** | Reads the *whole* paper (map-reduce) into one connected, undergrad-level explanation |
| **Verification** | LLM judge that scores the understanding's coverage & faithfulness |
| **Tutor** | Answers follow-up questions grounded in RAG-retrieved passages + the understanding |
| **Memory** | Keeps a running memory of the whole learning conversation so nothing is forgotten in long sessions |

> See [project_structure.md](project_structure.md) for the full architecture and code layout.

## Tech Stack

- **Orchestration:** LangGraph
- **LLMs:** Groq (`llama-3.1-8b-instant` by default; selectable in the UI) for review & Q&A; optional NVIDIA DeepSeek (`deepseek-v4-pro`/`-flash`) for the accuracy-critical Learn steps, routed via a multi-provider pool (`agents/llm_pool.py`)
- **RAG:** sentence-transformers embeddings with a scikit-learn TF-IDF fallback
- **UI:** Streamlit (math rendered as LaTeX/KaTeX)
- **Data:** arXiv API, pypdf
- **Evaluation:** `eval/` harness + metrics

---

## Getting Started (Local)

### 1. Clone the repository

```bash
git clone https://github.com/priyadip/Multi-Agent-System-Research-Paper-Reviewer.git
cd Multi-Agent-System-Research-Paper-Reviewer
```

### 2. Create and activate a virtual environment

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure your API keys

Create a `.env` file in the project root:

```env
# Required: drives the review pipeline and Learn Q&A
GROQ_API_KEY="gsk_your_key_here"
MODEL_NAME=llama-3.1-8b-instant

# Optional: accuracy-critical Learn steps on NVIDIA DeepSeek
NVIDIA_API_KEY="nvapi_your_key_here"
```

> - **Groq (required):** get a free key at the [Groq Console](https://console.groq.com/keys) → **API Keys** → **Create API Key**. It runs the review pipeline and the Learn tab's Q&A.
> - **NVIDIA (optional):** get a free key at [build.nvidia.com](https://build.nvidia.com). If set, the Learn subsystem routes Understanding to `deepseek-v4-pro` and Verification to `deepseek-v4-flash` (via the multi-provider pool), retrying with backoff and falling back to Groq. Without it, everything runs on Groq. In the UI you can paste **two** NVIDIA keys (one per model) in the sidebar; for local `.env` use, a single `NVIDIA_API_KEY` is enough.

*Note: the hosted Streamlit app does not use `.env`; visitors paste their own key(s) in the sidebar instead.*

---

## Usage

### Streamlit Web UI

```bash
streamlit run ui/app.py
```

Then open the local URL Streamlit prints (usually `http://localhost:8501`), enter an arXiv ID, and click **Review**.

### Command Line

Review a single paper by arXiv ID:

```bash
python agents/orchestrator.py --arxiv-id 1706.03762
```

Run the guided examples (basic review, batch, comparison, report export):

```bash
python example_usage.py
```

### MCP Server

Expose the reviewer as **MCP tools** (`review_paper`, `get_paper_metadata`) so an MCP client (Claude Desktop, Claude Code, Cursor, …) can call it. The server loads your `.env`, so a valid `GROQ_API_KEY` there is enough; set `NVIDIA_API_KEY` too and it routes through the multi-provider pool. Copy `mcp-server/claude_desktop_config.example.json` into your client config (fix the paths), restart, and ask it to review an arXiv ID. See [mcp-server/README.md](mcp-server/README.md) for full setup.

### Evaluation

The harness in `eval/` runs each test case (an arXiv ID + an expected outcome + constraints) through the full LangGraph pipeline, times it, and checks the result. A case passes only if the status matches the expectation **and** no constraint is violated, including a content check that flags a "success" whose text is merely LLM error strings (e.g. an invalid key or rate-limit run).

```bash
python eval/run_eval.py --output eval/eval_results.json
```

It reports the **success rate**, a **latency distribution** (mean, median, std, min/max, p95/p99), **tool-call stats**, **constraint violations**, and a **per-agent efficiency profile** (average tool calls + latency per agent), all computed by `eval/metrics.py` from the per-agent metrics the orchestrator records at each node (`report["metrics"]["per_agent"]`).

**Latest run** (8 cases, live Groq free tier): **100% pass, 0 violations, 14 tool calls/review**. Latency averages ~91 s/review, dominated by free-tier rate-limit backoff rather than pipeline cost. All three negative cases are correctly returned as errors rather than hallucinated into reviews: an invalid ID, an empty ID, and a **deliberately fake but real-looking ID** (`2402.99999`).

---

## Project Structure

```
├── agents/
│   ├── base_agent.py          # Groq client + call_llm (with retry/backoff)
│   ├── reader_agent.py        # arXiv metadata + PDF extraction
│   ├── meta_reviewer_agent.py # Methodology & contribution
│   ├── critic_agent.py        # Strengths / weaknesses / improvements
│   ├── cite_agent.py          # Reference count + in-text citations
│   ├── publication_agent.py   # Venue detection (paused)
│   ├── orchestrator.py        # LangGraph review workflow (+ per-agent metrics)
│   ├── understanding_agent.py # Whole-paper comprehension (Learn)
│   ├── verification_agent.py  # Coverage/faithfulness judge (Learn)
│   ├── learning_agent.py      # Tutor: explanations + RAG Q&A (Learn)
│   ├── memory_agent.py        # Running conversation memory (Learn)
│   ├── rag_store.py           # PaperRAG: chunk + embed + retrieve
│   └── llm_pool.py            # Multi-provider routing + retry + failover
├── ui/app.py                  # Streamlit application
├── eval/
│   ├── run_eval.py            # Harness: run suite, check constraints
│   ├── metrics.py             # Success rate, latency, per-agent efficiency
│   └── test_cases.json        # Test suite (real IDs + error cases)
├── mcp-server/                # Model Context Protocol (MCP) server
├── example_usage.py           # CLI demo / batch processing
└── requirements.txt           # Python dependencies
```

See **[project_structure.md](project_structure.md)** for the architecture diagrams and design notes.

## License

Released under the MIT License.

## Author

**Priyadip Sau** · [website](https://priyadipsau.in/) · saupriyadip571@gmail.com
