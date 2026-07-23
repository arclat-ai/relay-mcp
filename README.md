# Relay — AI Agent Latency Auditor

Relay is an MCP server that plugs into Claude Code and audits your AI agent codebase for latency bottlenecks. It reads your actual source code, ranks issues by impact, and can apply fixes directly from Claude Code.

Relay is a product of the **Arclat** studio. Learn more at [relay.arclat.com](https://relay.arclat.com).

## Install Relay

1. Get your free API key at [relay.arclat.com](https://relay.arclat.com)
2. Add to your Claude Code MCP config (`~/.claude/claude_code_config.json`):

```json
{
  "mcpServers": {
    "relay": {
      "command": "uvx",
      "args": ["relay-mcp"],
      "env": {
        "RELAY_API_KEY": "your_key_here"
      }
    }
  }
}
```

3. In Claude Code, say: `"Audit this codebase for latency issues"`
4. Done.

Each audit also writes a `relay-report.json` file into the audited directory. Upload it to the [Relay dashboard](https://relay.arclat.com/dashboard) (invited access) for the full analytics view.

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
| `audit_codebase`  | Reads Python files in a directory, returns ranked findings (each with a verification verdict) and writes `relay-report.json` |
| `get_findings`    | Filters findings from last audit by severity, type, or verification status |
| `verify_audit`    | Shows which findings the semantic pass confirmed vs dismissed, with reasons |
| `apply_fix`       | Applies a fix (dry_run=true by default; file path defaults to the finding's file) |
| `usage_status`    | Shows your plan and audits used / remaining this month   |

The last audit is persisted to `~/.relay/last-audit.json`, so `get_findings`,
`verify_audit`, and `apply_fix` keep working after an MCP server restart.

## What it detects

- **SyncOutput** — LLM calls missing streaming (`stream=True`), including calls that forward `**kwargs`
- **SequentialTools** — consecutive data-independent awaits that should use `asyncio.gather()`
- **CacheMiss** — the same fully-static LLM call repeated at multiple call sites with no caching
- **BlockingIO** — sync `requests` / DB calls, plus `time.sleep` and blocking `subprocess` calls inside async functions
- **ColdStart** — API clients (`OpenAI`, `httpx.Client`, `aiohttp.ClientSession`, …) constructed per-request instead of at startup
- **Prefetch** — predictable tool-call pairs that could be started speculatively

Every finding then goes through a **verification pass** that re-reads the flagged
site in context and either confirms it as a real latency gap or dismisses it as a
false positive — with a one-line reason either way.

## CLI

The same engine ships as a `relay` command:

```bash
relay scan   <dir>          # structural pass — flag candidate latency patterns
relay verify <dir>          # semantic pass — keep only confirmed gaps
relay report <dir> [-o f]   # write relay-report.json for the dashboard
relay mcp                   # run the MCP server (same as relay-mcp)
```

`scan` and `verify` accept `--json` for machine-readable output (CI, jq).
`verify` also accepts `--fail-on {none,high,any}` so it can gate a pipeline —
`relay verify . --fail-on high` exits non-zero when a confirmed high-impact
latency gap remains.

## Repository structure

```
relay-mcp/
├── mcp_server/          # MCP server (ships as relay-mcp on PyPI)
│   ├── server.py        # entry point, exposes 5 MCP tools
│   ├── engine/          # audit engine (detectors, scorer, code_parser)
│   └── usage/           # SQLite-based usage tracker
├── api/ (backend/)      # lightweight FastAPI — auth + billing only
├── frontend/            # Next.js 14 landing page + dashboard
└── pyproject.toml       # package config for uvx/pip install
```

## Environment variables

| Variable         | Purpose                                              |
|------------------|------------------------------------------------------|
| `RELAY_API_KEY`  | Your Relay API key (`rly_...`)                        |
| `RELAY_API_URL`  | Override the billing/usage sync endpoint             |

Legacy `ARCLAT_API_KEY` / `ARCLAT_API_URL` are still read as a fallback.

## Development

```bash
# Install MCP server in editable mode
pip install -e ".[dev]"

# Run FastAPI backend
cd backend && uvicorn app.main:app --reload

# Run Next.js frontend
cd frontend && npm run dev
```
