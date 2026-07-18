# Multi-Agent Research Paper Reviewer

A sophisticated multi-agent system for reviewing academic papers using LangGraph orchestration and Groq API.

## Architecture Overview

```
┌─────────────────┐
│  MCP Client     │ ← Input arXiv ID
└────────┬────────┘
         │
    ┌────▼───────┐
    │Orchestrator│
    └────┬───────┘
         │
    ┌────┴────────────────────────┐
    │                             │
┌───▼────┐  ┌────────┐  ┌───────┐  ┌─────────┐
│ Reader │→ │Meta    │→ │Critic │→ │Cite     │
│ Agent  │  │Reviewer│  │Agent  │  │Agent    │
└────────┘  └────────┘  └───────┘  └─────────┘
    ↓           ↓          ↓            ↓
[Extract]   [Analyze]  [Critique]  [Citations]
```

## Setup Instructions

### Prerequisites
- Python 3.9+
- Groq API Key

### Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

May be its takes more than 15 minutes, so you have to wait until the full process is completed.


# Edit .env and add your GROQ_API_KEY


### Environment Variables

The application requires API keys to function.

  Add your Groq API key to the `.env` file:

    ```
    GROQ_API_KEY="your_groq_api_key_here"
    ```


# Environment Setup

This project requires environment variables to authenticate with the Groq API and configure the model used for all agents.

## Environment Variables

Create a `.env` file in the project root and add:

```env
GROQ_API_KEY="your_groq_api_key_here"
MODEL_NAME=llama-3.1-8b-instant
```

## How to Obtain Your Groq API Key

Follow these steps to generate your API key:

1. Visit the [Groq Console](https://console.groq.com/docs/model/llama-3.1-8b-instant)
2. Log in using your email ID
3. In the top-right corner, click on **API Keys**
4. Click **Create API Key**, give it a name, and press Enter
5. Copy the generated key and paste it into your `.env` file

## Example `.env` File

```env
GROQ_API_KEY="gsk_XXXXXXXXXXXXXXXXXXXXXXXX"
MODEL_NAME=llama-3.1-8b-instant
```

## Notes

- Keep your API key secure and never commit it to version control





##  Running the System



### 1. Run the Multi-Agent System

```bash
python agents/orchestrator.py --arxiv-id 2301.12345
```

### 2. Run with UI 

```bash
streamlit run ui/app.py
```


# UI Instructions

After entering the arXiv ID in the input field, click on **Review**.

The system will start processing the paper through all agents.

Once processing is complete, scroll to the bottom of the page to view the full results, including:

- Reader output
- Meta-review
- Critic analysis
- Citation analysis
- Final report

## Notes on Publication Agent

We attempted to build a fully functional Publication Agent capable of:

- Extracting venue information from arXiv metadata
- Detecting publication details from PDF headers
- Performing smart web search for confirmation

However, due to API key limitations and rate restrictions, the external search tools could not be used reliably.

For this reason, the **Publication Agent currently returns a placeholder response** and is effectively skipped in the workflow.

This ensures the rest of the pipeline works correctly without breaking the orchestrator flow.

## Notes on Diagram Generation Agent

We also experimented with creating a Diagram Generation Agent to automatically generate architecture diagrams and visual summaries.

But due to the same API limitations and external dependency issues, this agent was removed from the final implementation to maintain system stability.





## Project Structure

```
multi-agent-paper-reviewer/
├── agents/
│   ├── __init__.py
│   ├── base_agent.py          # Base agent class
│   ├── reader_agent.py        # Extracts paper content
│   ├── meta_reviewer_agent.py # Comprehensive analysis
│   ├── critic_agent.py        # Critical evaluation
│   ├── cite_agent.py          # Citation analysis
│   └── orchestrator.py        # LangGraph orchestration
├── mcp-server/
│   ├── __init__.py
│   ├── server.py              # MCP server implementation
│   └── tools.py               # MCP tools 
├── eval/
│   ├── test_cases.json        # Test cases
│   ├── run_eval.py            # Evaluation script
│   └── metrics.py             # Metrics computation
├── ui/
│   └── app.py                 # Streamlit UI
├── requirements.txt
├── .env
├── README.md
├── ARCH.md
└── research_note.pdf
```

## Agent Roles

### 1. Reader Agent
- **Role**: Extract and summarize paper content
- **Tools**: PDF extractor, arXiv API
- **Output**: Structured summary with key points

### 2. Meta-Reviewer Agent
- **Role**: Comprehensive quality analysis
- **Tools**: Text analyzer, metrics calculator
- **Output**: Overall assessment with scores

### 3. Critic Agent
- **Role**: Identify strengths and weaknesses
- **Tools**: Weakness detector, comparison tool
- **Output**: Detailed critique with recommendations

### 4. Cite Agent
- **Role**: Analyze citations and references
- **Tools**: Citation extractor, reference validator
- **Output**: Citation network and impact analysis

## Testing

Run the evaluation suite:

```bash
python eval/run_eval.py
```

This will:
- Run 6+ test cases
- Compute metrics (success rate, latency, tool calls)
- Generate evaluation report

## Metrics

- **Success Rate**: Percentage of successfully reviewed papers
- **Average Latency**: Time taken per review
- **Tool Call Count**: Number of tool invocations
- **Constraint Violations**: Violations of review guidelines
- **Quality Score**: Aggregate quality metric

## Key Assumptions

1. Papers are accessible via arXiv API or local storage
2. All agents use Groq's Llama-3.1-8b-instant model
3. Reviews are for student comprehension (not publication)
4. System processes one paper at a time
5. Internet connection required for API access



## Contributors

[Priyadip Sau]
