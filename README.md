# Multi-Agent Research Paper Reviewer

> **Live demo:** paste your own free [Groq API key](https://console.groq.com/keys) in the sidebar to run a review. The key is used only for your session and is never stored.
>
> **Deploy your own (free):** on [Streamlit Community Cloud](https://share.streamlit.io) → *New app* → this repo → main file `ui/app.py`.

This project is an AI-powered multi-agent system for conducting comprehensive reviews of academic papers from arXiv. It uses a team of specialized AI agents, orchestrated by LangGraph, to perform tasks like reading, summarizing, critiquing, and analyzing citations.

## Features

- **Multi-Agent Architecture:** Specialized agents for reading, critiquing, citation analysis, and more.
- **Dual Interfaces:** Use the rich, interactive Streamlit web UI or the flexible command-line script.
- **In-Depth Analysis:** Goes beyond summarization to provide critical analysis, including strengths, weaknesses, and suggested improvements.
- **Citation & Publication Data:** Analyzes paper citations and searches for official publication venues.
- **Extensible:** Built with a modular architecture that is easy to extend.

## Setup Instructions

Follow these steps to get the project running on your local machine.

### 1. Clone the Repository

Not Requird, as you have full file.


### 2. Create and Activate a Virtual Environment

It is highly recommended to use a virtual environment to manage project dependencies.

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

### 3. Install Dependencies

Install all the required Python packages using the `requirements.txt` file.

```bash
pip install -r requirements.txt
```
May be its takes more than 15 minutes, so you have to wait until the full process is completed.

### 4. Configure Environment Variables

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




## How to Run

You can run the project using either the Streamlit Web UI or the command-line script.

### Using the Streamlit Web UI 
The web UI provides a rich, interactive experience with real-time progress updates.

To start the Streamlit server, run the following command:

```bash
streamlit run ui/app.py
```

Now, open your web browser and navigate to the local URL provided by Streamlit (usually `http://localhost:8501`).


###  Run the Multi-Agent System

```bash
python agents/orchestrator.py --arxiv-id 2301.12345
```

### Using the Command-Line Script

The `example_usage.py` script demonstrates the core functionality of the agent system and allows for batch processing.

To run the script, use:

```bash
python example_usage.py
```

The script will guide you through several examples, from a basic review to saving formatted reports.

## Project Structure

- **/agents**: Contains the core logic for all AI agents and the orchestrator graph.
- **/ui**: The Streamlit application code.
- **/eval**: Scripts and data for evaluating the performance of the agents.
- **/mcp-server**: A server for the Multi-Agent Collaboration Protocol (MCP).
- **example_usage.py**: A command-line script for demonstrating and testing the system.
- **requirements.txt**: A list of all Python dependencies.

