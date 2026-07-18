# Architecture Document

## System Overview

The Multi-Agent Research Paper Reviewer is a distributed system that uses multiple specialized AI agents coordinated through LangGraph to provide comprehensive reviews of academic papers from arXiv.

## Agent Roles

### 1. Reader Agent
**Responsibility**: Extract and summarize paper content from arXiv

**Tools**:
- arXiv API client for metadata retrieval
- Text extraction from abstracts
- LLM-based summarization

**Input**: arXiv paper ID
**Output**: Paper metadata, abstract, key points summary

### 2. Meta-Reviewer Agent
**Responsibility**: Provide comprehensive quality analysis

**Tools**:
- Methodology analyzer
- Contribution evaluator
- Overall review synthesizer

**Input**: Paper information from Reader Agent
**Output**: Methodology analysis, contribution evaluation, overall review with scoring

### 3. Critic Agent
**Responsibility**: Identify strengths, weaknesses, and provide constructive criticism

**Tools**:
- Strength identifier
- Weakness detector
- Improvement suggester

**Input**: Paper information and meta-review
**Output**: List of strengths, weaknesses, improvement suggestions, critique summary

### 4. Cite Agent
**Responsibility**: Analyze citations and references

**Tools**:
- Citation extractor (regex-based)
- Context analyzer
- Reference quality evaluator
- Recommendation generator

**Input**: Paper information
**Output**: Citation count, context analysis, quality assessment, reading recommendations

### 5. Publication Agent
**Responsibility**: Discover the official publication venue of the paper

**Tools**:
- Web search tool (e.g., Tavily, Google Search API)
- Information extractor

**Input**: Paper title and authors
**Output**: Publication status, venue name, and a link to the publication if found


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
  "role": "Extract paper content from arXiv",
  "tool_calls": 2,
  "output": {
    "status": "success",
    "arxiv_id": "string",
    "paper_title": "string",
    "authors": ["string"],
    "categories": ["string"],
    "metadata": {
      "title": "string",
      "abstract": "string",
      "published": "string",
      "pdf_url": "string"
    },
    "key_points": {
      "summary": "string",
      "abstract_length": number
    }
  }
}
```

### Meta-Reviewer Agent Output
```json
{
  "agent": "MetaReviewerAgent",
  "role": "Comprehensive quality analysis",
  "tool_calls": 3,
  "output": {
    "status": "success",
    "paper_title": "string",
    "methodology_analysis": {
      "methodology_analysis": "string"
    },
    "contribution_evaluation": {
      "contribution_evaluation": "string"
    },
    "overall_review": "string"
  }
}
```

### Critic Agent Output
```json
{
  "agent": "CriticAgent",
  "role": "Critical evaluation",
  "tool_calls": 3,
  "output": {
    "status": "success",
    "paper_title": "string",
    "strengths": ["string"],
    "weaknesses": ["string"],
    "improvements": "string",
    "critique_summary": "string"
  }
}
```

### Cite Agent Output
```json
{
  "agent": "CiteAgent",
  "role": "Citation analysis",
  "tool_calls": 4,
  "output": {
    "status": "success",
    "paper_title": "string",
    "extracted_citations": ["string"],
    "citation_count": number,
    "citation_context": {
      "citation_context": "string"
    },
    "reference_quality": {
      "reference_quality": "string",
      "citation_count_estimate": number
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
  "summary": {
    "key_points": {},
    "abstract": "string"
  },
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
    "citation_count": number,
    "context": {},
    "quality": {},
    "recommendations": "string"
  },
  "metrics": {
    "total_tool_calls": number,
    "duration_seconds": number,
    "agents_executed": number
  }
}
```

## Workflow Architecture

```
┌─────────────────────────────────────────────────────┐
│                   MCP Client                        │
│              (Input: arXiv ID)                      │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│              LangGraph Orchestrator                 │
│                                                     │
│   ┌──────────────────────────────────────┐          │
│   │  State Management                    │          │
│   │  - arxiv_id                          │          │
│   │  - agent outputs                     │          │
│   │  - timestamps                        │          │
│   │  - error tracking                    │          │
│   └──────────────────────────────────────┘          │
└──────┬──────────┬──────────┬──────────┬─────────────┘
       │          │          │          │
       ▼          ▼          ▼          ▼
┌──────────┐ ┌───────────┐ ┌──────────┐ ┌──────────┐
│  Reader  │→│   Meta-   │→│  Critic  │→│   Cite   │
│  Agent   │ │ Reviewer  │ │  Agent   │ │  Agent   │
└────┬─────┘ └─────┬─────┘ └────┬─────┘ └────┬─────┘
     │             │            │            │
     │ Tools:      │ Tools:     │ Tools:     │ Tools:
     │ - arXiv API │ - Method   │ - Strength │ - Citation
     │ - Extractor │   Analyzer │   Finder   │   Extractor
     │             │ - Contrib  │ - Weakness │ - Context
     │             │   Eval     │   Detector │   Analyzer
     │             │ - Review   │ - Improver │ - Quality
     │             │   Synth    │            │   Eval
     └─────────────┴────────────┴────────────┴
                       │
                       ▼
              ┌──────────────────┐
              │   Final Report   │
              │   Compilation    │
              └──────────────────┘
```

## MCP Server Integration

The system exposes two main tools through the MCP server:

1. **review_paper**: Full multi-agent review
2. **get_paper_metadata**: Quick metadata retrieval

MCP clients can invoke these tools programmatically for integration with other systems.

## Technology Stack

- **LLM**: Groq Llama-3.1-8b-instant
- **Orchestration**: LangGraph
- **MCP**: Model Context Protocol for tool exposure
- **API**: arXiv API for paper retrieval
- **UI**: Streamlit (optional)

## Key Design Decisions

1. **Sequential Agent Execution**: Agents execute in sequence rather than parallel to build upon each other's outputs
2. **Stateful Workflow**: LangGraph maintains state across agent executions
3. **Tool-based Architecture**: Each agent uses specific tools for its tasks
4. **MCP Integration**: System exposed as MCP server for programmatic access
5. **Student-focused**: All outputs optimized for student comprehension

## Contracts

### Agent Contract
All agents must:
- Inherit from BaseAgent
- Implement process() method
- Return standardized output format
- Track tool call counts
- Handle errors gracefully

### Tool Contract
All tools must:
- Accept standardized input
- Return JSON-serializable output
- Track invocation counts
- Handle API failures

## Assumptions

1. Papers are publicly available on arXiv
2. Internet connectivity is available
3. Groq API key is valid and has sufficient credits
4. Papers have standard academic structure
5. Abstract is sufficient for comprehensive analysis
6. Student audience needs simplified explanations