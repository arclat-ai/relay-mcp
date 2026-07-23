# Relay - AI Agent Latency Auditor

Relay is an open-source MCP server (and CLI) that audits AI agent and voice-agent
codebases for latency bottlenecks. It reads your actual source with an AST engine, ranks
issues by impact, runs a verification pass to drop false positives, and can apply fixes
directly from Claude Code.

No account, no API key, no backend - it runs entirely on your machine.

Relay is a product of the **Arclat** studio. Learn more at [relay.arclat.com](https://relay.arclat.com).

---

## Features

- **AST-based detection.** Parses your Python with the real grammar, not regexes, so it
  understands async/await, call targets, keyword arguments, and `**kwargs` forwarding.
- **Six latency detectors.** Streaming gaps, sequential tool calls, cache misses,
  blocking I/O in async code, per-request client construction, and prefetch
  opportunities (see [What it detects](#what-it-detects)).
- **Verification pass.** Every candidate is re-read in context and either confirmed as a
  real gap or dismissed as a false positive, each with a one-line reason.
- **Impact ranking.** Findings are scored and sorted so the highest-impact fixes surface
  first.
- **Apply fixes from Claude Code.** `apply_fix` rewrites the flagged site (dry-run by
  default) so you can review before writing.
- **Runs as MCP or CLI.** The same engine backs the Claude Code tools and the `relay`
  command, so agent output and terminal output never diverge.
- **CI gate.** `relay verify --fail-on high` exits non-zero when a confirmed high-impact
  gap remains, so it can fail a pipeline.
- **Dashboard reports.** Each audit writes a `relay-report.json` you can upload to the
  [Relay dashboard](https://relay.arclat.com/dashboard) for a full visual analytics view.
- **Zero runtime dependencies to speak of.** Just the `mcp` package - no network calls,
  no telemetry, nothing leaves your machine.
- **Persistent state.** The last audit is cached at `~/.relay/last-audit.json`, so
  `get_findings`, `verify_audit`, and `apply_fix` keep working across MCP restarts.

---

## Install (Claude Code / MCP)

Add Relay to your Claude Code MCP config (`~/.claude/claude_code_config.json`):

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

Then, in Claude Code, say: `"Audit this codebase for latency issues"`. That's it - no
key to configure.

Each audit writes `relay-report.json` into the audited directory. Upload it to the
[Relay dashboard](https://relay.arclat.com/dashboard) for the full analytics view.

---

## MCP tools

| Tool             | Description                                                                                          |
|------------------|------------------------------------------------------------------------------------------------------|
| `audit_codebase` | Reads Python files in a directory, returns ranked findings (each with a verification verdict) and writes `relay-report.json`. |
| `get_findings`   | Filters findings from the last audit by severity, type, or verification status.                      |
| `verify_audit`   | Shows which findings the semantic pass confirmed vs dismissed, with reasons.                         |
| `apply_fix`      | Applies a fix (`dry_run=true` by default; file path defaults to the finding's file).                 |

The last audit is cached at `~/.relay/last-audit.json`, so `get_findings`,
`verify_audit`, and `apply_fix` keep working after an MCP server restart.

---

## CLI

The same engine ships as a `relay` command:

```bash
relay scan   <dir>          # structural pass - flag candidate latency patterns
relay verify <dir>          # semantic pass  - keep only confirmed gaps
relay report <dir> [-o f]   # write relay-report.json for the dashboard
relay mcp                   # run the MCP server (same as relay-mcp)
```

- `scan` and `verify` accept `--json` for machine-readable output (CI, jq).
- `verify` accepts `--fail-on {none,high,any}` to gate a pipeline. For example,
  `relay verify . --fail-on high` exits non-zero when a confirmed high-impact latency
  gap remains.

### Use in CI

```yaml
- run: pip install relay-mcp
- run: relay verify . --fail-on high
```

---

## What it detects

| Detector          | What it flags                                                                                       |
|-------------------|------------------------------------------------------------------------------------------------------|
| **SyncOutput**    | LLM calls missing streaming (`stream=True`), including calls that forward `**kwargs`.                 |
| **SequentialTools** | Consecutive data-independent awaits that should run under `asyncio.gather()`.                       |
| **CacheMiss**     | The same fully-static LLM call repeated at multiple call sites with no caching.                       |
| **BlockingIO**    | Sync `requests` / DB calls, plus `time.sleep` and blocking `subprocess` calls inside async functions. |
| **ColdStart**     | API clients (`OpenAI`, `httpx.Client`, `aiohttp.ClientSession`, ...) built per-request instead of at startup. |
| **Prefetch**      | Predictable tool-call pairs that could be started speculatively.                                      |

### Verification pass

Every finding goes through a verification pass that re-reads the flagged site in context
and either confirms it as a real latency gap or dismisses it as a false positive, with a
one-line reason either way. The summary counts (`flagged`, `confirmed`, `dismissed`,
`confirmed_high_impact`) drive both the CLI output and the `--fail-on` CI gate.

---

## The dashboard

Relay itself is fully local. If you want a visual view of a report, the
[Relay dashboard](https://relay.arclat.com/dashboard) lets you drag in any
`relay-report.json` and browse the findings, severity breakdown, and time-lost
aggregates. The report never leaves your browser - it's parsed client-side.

---

## Environment variables

| Variable        | Purpose                                                          |
|-----------------|------------------------------------------------------------------|
| (none required) | Relay needs no configuration - it runs offline with no API key.  |

---

## Repository structure

```
relay-mcp/
├── mcp_server/          # MCP server + CLI (ships as relay-mcp on PyPI)
│   ├── server.py        # entry point, exposes the MCP tools
│   ├── cli.py           # `relay` command (scan / verify / report / mcp)
│   └── engine/          # audit engine (detectors, scorer, verify, code_parser)
├── tests/               # end-to-end engine tests
├── run.sh / run.ps1     # dev runners (install / register / test / serve)
└── pyproject.toml       # package config for uvx/pip install
```

---

## Development

```bash
# Install the MCP server + CLI in editable mode with dev deps
pip install -e ".[dev]"

# Run the test suite
pytest

# Run the audit engine on a directory directly
relay scan .
```

See [RUNNING.md](RUNNING.md) for the full dev workflow.

---

## License
[MIT](LICENSE)
