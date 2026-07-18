"""
MCP Server implementation for the multi-agent paper reviewer.
"""

import json
import asyncio
from typing import Any, Dict
from mcp.server.models import InitializationOptions
from mcp.server import Server, NotificationOptions
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import sys
import os

# Add parent directory to path to import agents
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.orchestrator import PaperReviewOrchestrator

# Initialize server
app = Server("paper-reviewer-mcp")
orchestrator = None


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
        orchestrator = PaperReviewOrchestrator()
    
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
            reader = ReaderAgent()
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