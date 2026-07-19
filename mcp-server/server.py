"""
MCP Server implementation for the multi-agent paper reviewer.
"""

import json
import asyncio
from typing import Any, Optional, Tuple
import sys
import os

from dotenv import load_dotenv

# Load .env from the project root so the server works regardless of the working
# directory the MCP client launches it from.
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(_PROJECT_ROOT, ".env"))
sys.path.append(_PROJECT_ROOT)

from mcp.server.models import InitializationOptions
from mcp.server import Server, NotificationOptions
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from agents.orchestrator import PaperReviewOrchestrator

# Initialize server
app = Server("paper-reviewer-mcp")
orchestrator: Optional[PaperReviewOrchestrator] = None


def _build_orchestrator() -> Tuple[Optional[PaperReviewOrchestrator], Optional[str]]:
    """Construct the orchestrator from environment credentials.

    GROQ_API_KEY (required) drives the review pipeline. If NVIDIA_API_KEY is also
    present, calls route through the multi-provider pool (Groq primary, NVIDIA
    fallback, with retry) for resilience. Returns (orchestrator, error_message).
    """
    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        return None, ("GROQ_API_KEY is not set. Add it to the project .env file or "
                      "to the MCP server config's 'env' block.")

    nvidia_key = os.getenv("NVIDIA_API_KEY")
    if nvidia_key:
        try:
            from agents.llm_pool import LLMPool
            pool = LLMPool([("groq", groq_key), ("nvidia", nvidia_key)],
                           rotate=False, attempts_per_provider=2)
            return PaperReviewOrchestrator(llm_pool=pool), None
        except Exception as e:  # fall back to plain Groq if the pool can't build
            print(f"[mcp] pool init failed ({e}); using Groq only", file=sys.stderr)

    # model=None -> base_agent falls back to MODEL_NAME env, then a sane default.
    return PaperReviewOrchestrator(api_key=groq_key), None


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="review_paper",
            description="Review an academic paper from arXiv using multi-agent system",
            inputSchema={
                "type": "object",
                "properties": {
                    "arxiv_id": {
                        "type": "string",
                        "description": "The arXiv paper ID (e.g., '2301.12345')"
                    }
                },
                "required": ["arxiv_id"]
            }
        ),
        Tool(
            name="get_paper_metadata",
            description="Get metadata for an arXiv paper",
            inputSchema={
                "type": "object",
                "properties": {
                    "arxiv_id": {
                        "type": "string",
                        "description": "The arXiv paper ID"
                    }
                },
                "required": ["arxiv_id"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls."""
    global orchestrator

    if orchestrator is None:
        orchestrator, err = _build_orchestrator()
        if err or orchestrator is None:
            return [TextContent(type="text",
                                text=json.dumps({"error": err or "orchestrator unavailable"}))]

    if name == "review_paper":
        arxiv_id = arguments.get("arxiv_id", "")
        
        if not arxiv_id:
            return [TextContent(
                type="text",
                text=json.dumps({"error": "arxiv_id is required"})
            )]
        
        try:
            # Run review in background
            result = orchestrator.review_paper(arxiv_id)
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=json.dumps({"error": str(e)})
            )]
    
    elif name == "get_paper_metadata":
        arxiv_id = arguments.get("arxiv_id", "")
        
        if not arxiv_id:
            return [TextContent(
                type="text",
                text=json.dumps({"error": "arxiv_id is required"})
            )]
        
        try:
            from agents.reader_agent import ReaderAgent
            reader = ReaderAgent()  # base_agent reads GROQ_API_KEY from env
            metadata = reader.fetch_paper_metadata(arxiv_id)
            
            return [TextContent(
                type="text",
                text=json.dumps(metadata, indent=2)
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=json.dumps({"error": str(e)})
            )]
    
    return [TextContent(
        type="text",
        text=json.dumps({"error": f"Unknown tool: {name}"})
    )]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="paper-reviewer-mcp",
                server_version="1.0.0",
                capabilities=app.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )


if __name__ == "__main__":
    asyncio.run(main())