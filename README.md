# Multi-Agent Research Paper Reviewer

> **Live demo:** https://multi-agent-system-research-paper-reviewer.streamlit.app/
> Paste your own free [Groq API key](https://console.groq.com/keys) in the sidebar to run a review. The key is used only for your session and is never stored.

An AI-powered multi-agent system for reviewing academic papers from arXiv. A team of specialized agents, orchestrated with **LangGraph** and powered by **Groq** LLMs, reads a paper and produces a structured review: a summary, a quality assessment, a critical analysis, and a citation breakdown.

## Features

- **Multi-agent architecture** — specialized agents for reading, meta-review, critique, and citation analysis, coordinated by a LangGraph workflow.
- **Two interfaces** — an interactive Streamlit web UI with live progress, plus command-line scripts.
- **In-depth analysis** — goes beyond summarization to surface strengths, weaknesses, and concrete suggestions for improvement.
- **Citation analysis** — counts references in the bibliography and lists in-text citations with the surrounding context.
- **Learn tab (multi-agent RAG)** — three agents read the *whole* paper: an **Understanding** agent comprehends and connects all sections (map-reduce), a **Verification** agent scores coverage/faithfulness, and a **Tutor** answers follow-up questions grounded in passages retrieved from the entire paper via semantic RAG (with a lexical TF-IDF fallback). Math renders as LaTeX.
- **Bring your own keys** — Groq runs the review & Q&A (fast); two optional NVIDIA keys run the accuracy-critical Learn steps on DeepSeek. Nothing is stored server-side.
- **Accuracy-first routing** — Understanding uses NVIDIA `deepseek-v4-pro` (key 1), Verification uses `deepseek-v4-flash` (key 2). These retry with exponential backoff on NVIDIA's transient `503`/`404`/`429` (up to ~8×, since NVIDIA's free tier is ~40 RPM and returns "workers busy") and only fall back to Groq if all retries fail — so a review favours correctness over speed and never hard-fails.

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
- **LLM:** Groq (`llama-3.1-8b-instant` by default; selectable in the UI)
- **RAG:** sentence-transformers embeddings with a scikit-learn TF-IDF fallback
- **UI:** Streamlit (math rendered as LaTeX/KaTeX)
- **Data:** arXiv API, pypdf

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

### 4. Configure your Groq API key

Create a `.env` file in the project root:

```env
GROQ_API_KEY="gsk_your_key_here"
MODEL_NAME=llama-3.1-8b-instant
```

> Get a free key at the [Groq Console](https://console.groq.com/keys) → **API Keys** → **Create API Key**.
> Keep your key secret and never commit `.env` to version control (it is already in `.gitignore`).

*Note: the hosted Streamlit app does not use `.env` — visitors paste their own key in the sidebar instead.*

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

### Evaluation

```bash
python eval/run_eval.py
```

---

## Deploy Your Own (Free)

This app deploys on [Streamlit Community Cloud](https://share.streamlit.io) with no CI/CD setup — it auto-redeploys on every push to `main`:

1. Sign in at [share.streamlit.io](https://share.streamlit.io) with GitHub.
2. **Create app** → **Deploy from GitHub**.
3. Repository: this repo &nbsp;·&nbsp; Branch: `main` &nbsp;·&nbsp; Main file: `ui/app.py`.
4. Deploy. Visitors paste their own Groq key to run reviews.

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
│   ├── orchestrator.py        # LangGraph review workflow
│   ├── understanding_agent.py # Whole-paper comprehension (Learn)
│   ├── verification_agent.py  # Coverage/faithfulness judge (Learn)
│   ├── learning_agent.py      # Tutor: explanations + RAG Q&A (Learn)
│   └── rag_store.py           # PaperRAG: chunk + embed + retrieve
├── ui/app.py                  # Streamlit application
├── eval/                      # Evaluation harness, metrics, test cases
├── mcp-server/                # Model Context Protocol (MCP) server
├── example_usage.py           # CLI demo / batch processing
└── requirements.txt           # Python dependencies
```

See **[project_structure.md](project_structure.md)** for the architecture diagrams and design notes.

## License

Released under the MIT License.

## Author

**Priyadip Sau** — [website](https://priyadipsau.in/) · saupriyadip571@gmail.com
