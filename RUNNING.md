# Running Relay

Relay is a self-contained, open-source MCP server + CLI. There is no account, API
key, or backend to run - it reads your code locally and writes a report you can
open in the dashboard.

## Install locally (development)

```bash
# From the repo root
pip install -e ".[dev]"
```

This installs both the `relay` and `relay-mcp` commands (defined in `pyproject.toml`).

Convenience runners are also provided:

```bash
./run.sh install      # or:  .\run.ps1 install   (Windows)
./run.sh all          # install + register with Claude Code
```

## Add to Claude Code

Edit `~/.claude/claude_code_config.json`:

```json
{
  "mcpServers": {
    "relay": {
      "command": "uvx",
      "args": ["relay-mcp"]
    }
  }
}
```

For a local checkout, use `"command": "relay-mcp"` instead (after `pip install -e .`).
Restart Claude Code, then say: `"Audit this codebase for latency issues"`.

## MCP tools

- `audit_codebase(directory, write_report=true)` - scan a Python project, get ranked findings
- `get_findings(severity?, finding_type?, status?)` - filter results from the last audit
- `verify_audit()` - show which findings were confirmed vs dismissed
- `apply_fix(finding_rank, file_path?, dry_run=true)` - patch a file (dry run by default)

State from the last audit is cached at `~/.relay/last-audit.json`, so the read-only
tools keep working across MCP restarts.

## CLI

```bash
relay scan   <dir>          # structural pass - flag candidate latency patterns
relay verify <dir>          # semantic pass  - keep only confirmed gaps
relay report <dir> [-o f]   # write relay-report.json for the dashboard
relay mcp                   # run the MCP server (same as relay-mcp)
```

`relay verify . --fail-on high` exits non-zero as a CI gate. See the
[README](README.md) for the full flag list.

## Run the server directly (debugging)

```bash
python -m mcp_server.server     # or:  relay mcp   /   ./run.sh serve
```

The MCP server normally runs as a subprocess managed by Claude Code - you don't
start it manually in day-to-day use.

## Tests

```bash
pytest
```

## Publishing to PyPI (for `uvx relay-mcp`)

```bash
pip install build twine
python -m build
twine upload dist/*
```

Package name: `relay-mcp` (defined in `pyproject.toml`).
