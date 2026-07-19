# Architecture Document

## System Overview

The Multi-Agent Research Paper Reviewer uses a team of specialized AI agents,
coordinated through LangGraph, to review academic papers from arXiv and to teach
them. It has two subsystems that share one extraction of the paper:

1. **Review pipeline** (LangGraph, sequential): reads the paper and produces a
   structured review (summary, quality assessment, critique, citation analysis).
2. **Learn subsystem** (multi-agent RAG, on-demand): comprehends the whole paper,
   verifies that understanding, and answers follow-up questions grounded in the
   paper's own text.

All model calls route through a shared multi-provider LLM pool (Groq and NVIDIA),
so agents are decoupled from any single provider.

## Review-Pipeline Agents

### 1. Reader Agent
**Responsibility**: Fetch paper content from arXiv.

**Tools**:
- arXiv API client for metadata retrieval
- PDF download and full-text extraction (pypdf), page by page

**Input**: arXiv paper ID
**Output**: Paper metadata, abstract, key points, and the full extracted text
(reused by the Learn subsystem so the paper is fetched once)

### 2. Publication Agent
**Responsibility**: Placeholder for venue detection.

**Status**: Currently **paused** (no LLM or web-search call). It is kept in the
graph so the workflow stays intact and venue detection can be re-enabled later.

**Input**: Paper metadata
**Output**: Empty / placeholder publication info

### 3. Meta-Reviewer Agent
**Responsibility**: Provide a quality analysis.

**Tools**: methodology analyzer, contribution evaluator, overall-review synthesizer

**Input**: Paper information from the Reader Agent
**Output**: Methodology analysis, contribution evaluation, overall review

### 4. Critic Agent
**Responsibility**: Identify strengths and weaknesses and suggest improvements.

**Tools**: strength identifier, weakness detector, improvement suggester

**Input**: Paper information and the meta-review
**Output**: Strengths, weaknesses, improvement suggestions, critique summary

### 5. Cite Agent
**Responsibility**: Analyze citations and references (counts are rule-based, not
LLM-guessed, so they are reproducible).

**Tools**:
- Reference counter (locates the bibliography, strips arXiv IDs / URLs / DOIs,
  counts distinct bracketed indices or estimates author-year entries, sanity cap)
- In-text citation extractor (regex markers with a surrounding context window)
- LLM-based citation-context, reference-quality, and recommendation analysis

**Input**: Paper information (full text)
**Output**: Total references, in-text citations with context, citation context,
reference-quality assessment, reading recommendations

## Learn-Subsystem Agents (on-demand)

Runs from the UI's Learn tab on the already-extracted full text. Not part of the
LangGraph pipeline.

### Understanding Agent
Comprehends the whole paper by map-reduce: summarize each part (map), then
synthesize one connected, undergraduate-level explanation (reduce). Uses a large
output budget so long derivations are not truncated.

### Verification Agent
An LLM judge that scores the understanding against the per-part notes for coverage
and faithfulness, returning a strict `SCORE` (0-100), a gaps list, and a verdict.

### PaperRAG (retrieval store)
Chunks the whole paper into overlapping windows and indexes them with
sentence-transformer embeddings, falling back to a lexical TF-IDF index if the
embedding model is unavailable. Retrieves the top-k chunks per query by cosine
similarity.

### Learning Agent (Tutor)
Answers a learner's question grounded in three sources: the retrieved chunks, the
verified understanding, and the running conversation memory. Math renders as LaTeX.

### Memory Agent
Maintains a compact but complete rolling memory of the conversation so earlier
context is never dropped in a long session.

## Multi-Provider LLM Pool

Every model call (review and Learn) routes through one pool that wraps several
OpenAI-compatible providers (Groq and NVIDIA NIM):

- **Task-specific routing**: Review, Q&A, and Memory use Groq (fast); Understanding
  uses NVIDIA `deepseek-v4-pro`; Verification uses NVIDIA `deepseek-v4-flash`.
- **Accuracy-first retry**: each provider is retried on transient errors
  (`503`/`404`/`429`/timeout/empty) with exponential backoff before failing over.
- **Circuit breaker**: only auth/payment errors (`401`/`402`/`403`) are permanent
  and disable a provider for the session.
- Calls are strictly sequential; reasoning-model output is read from
  `reasoning_content` when the standard field is empty.

## Message Schema

### Input Message
```json
{
  "arxiv_id": "string"
}
```

### Reader Agent Output
```json
{
  "agent": "ReaderAgent",
  "role": "Fetch paper content from arXiv",
  "tool_calls": 2,
  "output": {
    "status": "success",
    "arxiv_id": "string",
    "paper_title": "string",
    "authors": ["string"],
    "categories": ["string"],
    "full_text": "string",
    "metadata": {
      "title": "string",
      "abstract": "string",
      "published": "string",
      "pdf_url": "string"
    },
    "key_points": {
      "summary": "string",
      "abstract_length": "number"
    }
  }
}
```

### Cite Agent Output
```json
{
  "agent": "CiteAgent",
  "role": "Citation analysis",
  "tool_calls": 6,
  "output": {
    "status": "success",
    "paper_title": "string",
    "total_references": "number",
    "reference_detection_method": "string",
    "in_text_citations": [{ "marker": "string", "context": "string" }],
    "in_text_citation_count": "number",
    "citation_count": "number",
    "citation_context": { "citation_context": "string" },
    "reference_quality": {
      "reference_quality": "string",
      "citation_count_estimate": "number"
    },
    "recommendations": "string"
  }
}
```

### Final Report Schema
```json
{
  "status": "success",
  "arxiv_id": "string",
  "paper_title": "string",
  "authors": ["string"],
  "categories": ["string"],
  "summary": { "key_points": {}, "abstract": "string" },
  "full_text": "string",
  "meta_review": {
    "methodology": {},
    "contribution": {},
    "overall_review": "string"
  },
  "critical_analysis": {
    "strengths": ["string"],
    "weaknesses": ["string"],
    "improvements": "string",
    "summary": "string"
  },
  "citation_analysis": {
    "citation_count": "number",
    "total_references": "number",
    "reference_detection_method": "string",
    "in_text_citation_count": "number",
    "in_text_citations": [{ "marker": "string", "context": "string" }],
    "context": {},
    "quality": {},
    "recommendations": "string"
  },
  "publication_info": {},
  "metrics": {
    "total_tool_calls": "number",
    "duration_seconds": "number",
    "agents_executed": 5,
    "per_agent": [
      { "agent": "string", "tool_calls": "number", "duration": "number" }
    ]
  }
}
```

## Workflow Architecture

```
        arXiv ID  (Streamlit UI, CLI, or MCP client)
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│              LangGraph Orchestrator                 │
│   Typed ReviewState: arxiv_id, per-agent outputs,   │
│   timestamps, error flag, per-agent metrics         │
└──────────────────────┬──────────────────────────────┘
                       │  (linear edges, error short-circuit)
                       ▼
  Reader → Publication → Meta-Reviewer → Critic → Cite → Finalize
   (full     (paused      (methodology   (str/wk)  (refs +   (compile
    PDF)      placeholder)  + contrib)              in-text)   report)
                                                                 │
                                                                 ▼
                                                        ┌──────────────┐
                                                        │ Final Report │
                                                        └──────────────┘

  Learn subsystem (on-demand, on the extracted full text):
  Understanding (map-reduce) → Verification (LLM judge) → PaperRAG index
                        follow-up Q → PaperRAG.retrieve → Tutor + Memory
```

## MCP Server Integration

The system is also exposed as an MCP server (`mcp-server/server.py`) with two tools:

1. **review_paper**: full multi-agent review
2. **get_paper_metadata**: quick metadata retrieval

The server loads credentials from the project `.env` (or the client config's `env`
block): `GROQ_API_KEY` is required, and if `NVIDIA_API_KEY` is present, calls route
through the multi-provider pool. If no key is set, tool calls return a clear error.

## Evaluation

An automated harness (`eval/`) runs a suite of arXiv papers through the full
pipeline and checks each result:

- **Constraints**: max duration, min/max tool calls, required report fields.
- **Content check**: a structurally-"successful" review whose text is only LLM error
  strings (invalid key, rate-limit) is flagged as a failure, so the success rate is
  trustworthy.
- **Metrics** (`eval/metrics.py`): success rate, latency distribution
  (mean/median/std/min/max/p95/p99), tool-call stats, constraint violations, and a
  per-agent efficiency profile computed from `metrics.per_agent`.

## Technology Stack

- **LLMs**: Groq (`llama-3.1-8b-instant` by default) for review and Q&A; optional
  NVIDIA DeepSeek (`deepseek-v4-pro` / `deepseek-v4-flash`) for the accuracy-critical
  Learn steps, via the multi-provider pool
- **Orchestration**: LangGraph
- **RAG**: sentence-transformers embeddings with a scikit-learn TF-IDF fallback
- **MCP**: Model Context Protocol for tool exposure
- **API / parsing**: arXiv API, pypdf
- **UI**: Streamlit (math rendered as LaTeX/KaTeX)

## Key Design Decisions

1. **Sequential agent execution**: agents run in sequence so each builds on prior outputs.
2. **Stateful workflow**: LangGraph maintains typed state, with error short-circuiting.
3. **Whole-paper coverage**: the pipeline reads full PDF text, and the Learn subsystem
   comprehends the entire paper (not just the abstract).
4. **Grounded, verified learning**: RAG grounds answers in the paper, and a verification
   agent scores the stored understanding before it is trusted.
5. **Accuracy-first routing**: accuracy-critical steps use strong reasoning models with
   retry and Groq fallback, trading latency for correctness.
6. **Reproducible citation counts**: rule-based reference counting rather than LLM guesses.
7. **Bring-your-own key**: per-session keys in the UI, or env/`.env` for CLI/MCP; nothing
   is stored server-side.

## Contracts

### Agent Contract
All agents must:
- Inherit from `BaseAgent`
- Implement the `process()` method
- Return the standardized output format
- Track tool-call counts (reset per run)
- Handle errors gracefully (return an error string rather than raising)

### Tool Contract
All tools must:
- Accept standardized input
- Return JSON-serializable output
- Handle API failures without crashing the pipeline

## Assumptions

1. Papers are publicly available on arXiv.
2. Internet connectivity is available.
3. A valid Groq API key is provided (NVIDIA key optional for the Learn subsystem).
4. Papers have a standard academic structure (headings, a reference section).
5. Full PDF text is available for analysis; the Learn subsystem reads the whole paper.
6. The audience is students, so outputs favor clear, simplified explanations.
