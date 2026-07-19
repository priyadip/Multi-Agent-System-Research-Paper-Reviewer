# MCP Server

Exposes the multi-agent paper reviewer as **MCP tools** so any MCP client
(Claude Desktop, Claude Code, Cursor, etc.) can call it. It wraps the same
`PaperReviewOrchestrator` used by the Streamlit UI and CLI.

## Tools

| Tool | Arguments | Returns |
|------|-----------|---------|
| `review_paper` | `arxiv_id` | Full multi-agent review report (JSON) |
| `get_paper_metadata` | `arxiv_id` | arXiv metadata only (title, authors, abstract, ...) |

## Credentials

The server loads the project's `.env` at startup, so if your root `.env` has a
valid `GROQ_API_KEY` it just works. You can also pass credentials via the client
config's `env` block (below), which overrides `.env`.

- `GROQ_API_KEY`: **required** (drives the review pipeline).
- `MODEL_NAME`: optional (defaults to `llama-3.1-8b-instant`).
- `NVIDIA_API_KEY`: optional. If set, calls route through the multi-provider
  pool (Groq primary, NVIDIA fallback, with retry) instead of Groq alone.

If `GROQ_API_KEY` is missing, tool calls return a clear error instead of failing
silently.

## Setup for Claude Desktop

1. Copy [`claude_desktop_config.example.json`](claude_desktop_config.example.json)
   into your Claude Desktop config file:
   - **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
   - **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
2. Fix the two absolute paths (`command`, `args`) for your machine, and set
   `GROQ_API_KEY`. (If your root `.env` already has the key, you may delete the
   whole `env` block.)
3. Restart Claude Desktop. Ask it: *"Use paper-reviewer to review arXiv 1706.03762."*

## Setup for Claude Code (CLI)

```bash
claude mcp add paper-reviewer -- \
  "D:\\Multi-Agent System_ Research Paper Reviewer\\venv\\Scripts\\python.exe" \
  "D:\\Multi-Agent System_ Research Paper Reviewer\\mcp-server\\server.py"
```

(The server reads `GROQ_API_KEY` from the project `.env`.)

## Run standalone (debug)

```bash
venv\Scripts\python.exe mcp-server\server.py
```

It speaks the MCP protocol over stdio and waits for a client; there is no
interactive prompt. Use it through an MCP client, not directly.

## Notes

- This server is a **standalone entry point**; the Streamlit app and CLI do not
  depend on it. Deleting this folder does not affect them.
- `review_paper` runs the full pipeline, so on the Groq free tier a single call
  can take a while (rate-limit backoff), same as a UI review.
