# Arclat — AI Agent Latency Auditor

Arclat is an MCP server that plugs into Claude Code and audits your AI agent codebase for latency bottlenecks. It reads your actual source code, ranks issues by impact, and can apply fixes directly from Claude Code.

## Install Arclat

1. Get your free API key at [arclat.com](https://arclat.com)
2. Add to your Claude Code MCP config (`~/.claude/claude_code_config.json`):

```json
{
  "mcpServers": {
    "arclat": {
      "command": "uvx",
      "args": ["arclat-mcp"],
      "env": {
        "ARCLAT_API_KEY": "your_key_here"
      }
    }
  }
}
```

3. In Claude Code, say: `"Audit this codebase for latency issues"`
4. Done.

## Usage limits

| Plan       | Price     | Limits                                      |
|------------|-----------|---------------------------------------------|
| Free       | $0        | 20 audits/month, findings only              |
| Pro        | $19/mo    | Unlimited audits + apply_fix tool           |
| Team       | $49/mo    | 5 seats + CI/CD GitHub Action               |
| Enterprise | $200+/mo  | Custom limits + Slack integration + support |

## MCP Tools

| Tool              | Description                                              |
|-------------------|----------------------------------------------------------|
| `audit_codebase`  | Reads Python files in a directory, returns ranked findings |
| `get_findings`    | Filters findings from last audit by severity or type     |
| `apply_fix`       | Applies a fix to a file (dry_run=true by default)        |

## What it detects

- **SyncOutput** — LLM calls missing streaming (`stream=True`)
- **SequentialTools** — independent tool calls that should use `asyncio.gather()`
- **CacheMiss** — repeated identical LLM calls with no caching
- **BlockingIO** — sync `requests.get` / DB calls blocking the event loop
- **ColdStart** — expensive init/setup functions running per-request
- **Prefetch** — predictable tool-call pairs that could be started speculatively

## Repository structure

```
arclat/
├── mcp_server/          # MCP server (ships as arclat-mcp on PyPI)
│   ├── server.py        # entry point, exposes 3 MCP tools
│   ├── engine/          # audit engine (detectors, scorer, code_parser)
│   └── usage/           # SQLite-based usage tracker
├── api/ (backend/)      # lightweight FastAPI — auth + billing only
├── frontend/            # Next.js 14 landing page + dashboard
└── pyproject.toml       # package config for uvx/pip install
```

## Development

```bash
# Install MCP server in editable mode
pip install -e ".[dev]"

# Run FastAPI backend
cd backend && uvicorn app.main:app --reload

# Run Next.js frontend
cd frontend && npm run dev
```
