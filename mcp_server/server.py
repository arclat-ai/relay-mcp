"""
Relay MCP Server
Run via: uvx relay-mcp  (or: python -m mcp_server.server)

Relay is the latency-auditor MCP, a product of the Arclat studio.
"""
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from mcp_server.engine.engine import AuditEngine
from mcp_server.usage.tracker import validate_and_check, increment

mcp = FastMCP("relay")

DASHBOARD_URL = "https://relay.arclat.com/dashboard"

# In-memory cache of last audit result for get_findings
_last_result = None


def _severity_icon(s: str) -> str:
    return {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(s.lower(), "⚪")


def _format_findings(bottlenecks: list) -> str:
    if not bottlenecks:
        return "No bottlenecks detected."
    lines = []
    for f in bottlenecks:
        icon = _severity_icon(f["severity"])
        loc = f["location"]
        loc_str = loc["display"] if isinstance(loc, dict) else loc
        lines.append(f"\n### {icon} [{f['rank']}] {f['title']}")
        lines.append(f"**Location:** {loc_str}")
        lines.append(f"**Severity:** {f['severity'].upper()}  |  **Time lost:** ~{f['time_lost_ms']}ms")
        lines.append(f"**Fix effort:** {f['effort']}  |  **Impact:** {f['impact']}")
        lines.append(f"\n{f['description']}")
        if f.get("code_before") and f.get("code_after"):
            lines.append(f"\n**Before:**\n```python\n{f['code_before']}\n```")
            lines.append(f"**After:**\n```python\n{f['code_after']}\n```")
    return "\n".join(lines)


def _write_report(result, directory: str) -> Path:
    """
    Persist the audit as a JSON report the Relay dashboard can load.

    Writes two files into the audited directory:
      - relay-report.json                      (always the latest run)
      - relay-report-<UTC timestamp>.json      (an immutable history copy)
    Upload either to https://relay.arclat.com/dashboard.
    """
    report = result.to_dict()
    report["generator"] = "relay-mcp"
    report["product"] = "relay"

    out_dir = Path(directory)
    if not out_dir.is_dir():
        out_dir = Path.cwd()

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    latest = out_dir / "relay-report.json"
    history = out_dir / f"relay-report-{stamp}.json"

    payload = json.dumps(report, indent=2)
    for target in (latest, history):
        try:
            target.write_text(payload, encoding="utf-8")
        except OSError:
            pass
    return latest


@mcp.tool()
def audit_codebase(directory: str, api_key: str = "") -> str:
    """
    Audit an AI agent codebase for latency bottlenecks.
    Reads Python files in the given directory and returns ranked findings with fix recommendations.

    Args:
        directory: Absolute path to the codebase directory to audit.
        api_key: Your Relay API key (rly_...). Get one at https://relay.arclat.com
    """
    global _last_result

    # Fall back to env var if not passed directly
    key = api_key or os.getenv("RELAY_API_KEY", "") or os.getenv("ARCLAT_API_KEY", "")

    allowed, reason = validate_and_check(key)
    if not allowed:
        return f"❌ {reason}"

    result = AuditEngine().run_on_codebase(directory)
    _last_result = result

    increment(key)

    report_path = _write_report(result, directory)

    summary = result.summary
    bottlenecks = result.to_dict()["bottlenecks"]

    header = (
        f"## Relay Audit Report\n"
        f"**{summary['total_bottlenecks']} bottleneck(s) found · "
        f"~{summary['estimated_improvement_pct']}% estimated improvement**\n"
        f"**Top issue:** {summary['top_issue']}\n"
        f"\n_Saved to `{report_path}` — upload it to {DASHBOARD_URL} for the full analytics view._\n"
    )

    return header + _format_findings(bottlenecks)


@mcp.tool()
def verify_findings(severity: str = "") -> str:
    """
    Run the verification pass over the last audit: trace each flagged candidate
    against its source context and keep only the ones that are real, actionable
    latency gaps. Dismissed candidates are listed with a one-line reason.

    Args:
        severity: Optional filter applied before verification ('high'/'medium'/'low').
    """
    from mcp_server.engine.verify import verify_findings as _verify

    if _last_result is None:
        return "No audit has been run yet. Call audit_codebase first."

    bottlenecks = _last_result.to_dict()["bottlenecks"]
    if severity:
        bottlenecks = [b for b in bottlenecks if b["severity"].lower() == severity.lower()]

    v = _verify(bottlenecks)
    s = v["summary"]
    lines = [
        "## Relay Verification",
        f"**{s['flagged']} flagged → {s['dismissed']} dismissed → "
        f"{s['confirmed']} confirmed ({s['confirmed_high_impact']} high-impact)**\n",
    ]
    confirmed = [g for g in v["findings"] if g["status"] == "confirmed"]
    dismissed = [g for g in v["findings"] if g["status"] == "dismissed"]
    if confirmed:
        lines.append("### Confirmed")
        for g in confirmed:
            loc = g["location"]
            loc = loc["display"] if isinstance(loc, dict) else loc
            lines.append(f"- **[{g['impact']}]** {g['title']} — {g['reason']}  ·  `{loc}`")
    if dismissed:
        lines.append("\n### Dismissed (false positives)")
        for g in dismissed:
            lines.append(f"- ✗ {g['title']} → {g['reason']}")
    if not confirmed:
        lines.append("\n✓ **0 real latency gaps** — every candidate dismissed.")
    return "\n".join(lines)


@mcp.tool()
def get_findings(severity: str = "", finding_type: str = "") -> str:
    """
    Return findings from the last audit, optionally filtered.

    Args:
        severity: Filter by severity — 'high', 'medium', or 'low'. Leave blank for all.
        finding_type: Filter by type e.g. 'sequential_tools', 'sync_output'. Leave blank for all.
    """
    if _last_result is None:
        return "No audit has been run yet. Call audit_codebase first."

    bottlenecks = _last_result.to_dict()["bottlenecks"]
    if severity:
        bottlenecks = [b for b in bottlenecks if b["severity"].lower() == severity.lower()]
    if finding_type:
        bottlenecks = [b for b in bottlenecks if b["type"].lower() == finding_type.lower()]

    if not bottlenecks:
        return "No findings match the given filters."
    return _format_findings(bottlenecks)


@mcp.tool()
def apply_fix(file_path: str, finding_rank: int, dry_run: bool = True) -> str:
    """
    Apply a fix recommendation to a file.

    Args:
        file_path: Absolute path to the file to modify.
        finding_rank: Rank number of the finding to fix (from audit_codebase output).
        dry_run: If True (default), show what would change without writing. Set to False to apply.
    """
    if _last_result is None:
        return "No audit has been run yet. Call audit_codebase first."

    bottlenecks = _last_result.to_dict()["bottlenecks"]
    match = next((b for b in bottlenecks if b["rank"] == finding_rank), None)
    if match is None:
        return f"No finding with rank {finding_rank}. Valid ranks: {[b['rank'] for b in bottlenecks]}"

    before = match.get("code_before", "")
    after = match.get("code_after", "")

    if not before or not after:
        return f"Finding '{match['title']}' does not have an automated fix. Apply manually:\n{match['description']}"

    try:
        source = open(file_path, encoding="utf-8").read()
    except FileNotFoundError:
        return f"File not found: {file_path}"

    if before not in source:
        return (
            f"Could not locate the exact pattern in {file_path}.\n"
            f"Apply manually — replace:\n```python\n{before}\n```\nwith:\n```python\n{after}\n```"
        )

    new_source = source.replace(before, after, 1)

    if dry_run:
        return (
            f"**Dry run — no changes written.**\n\n"
            f"File: `{file_path}`\n\n"
            f"**Before:**\n```python\n{before}\n```\n\n"
            f"**After:**\n```python\n{after}\n```\n\n"
            f"Call with `dry_run=False` to apply."
        )

    open(file_path, "w", encoding="utf-8").write(new_source)
    return f"✅ Fix applied to `{file_path}`.\n\nReplaced:\n```python\n{before}\n```\nWith:\n```python\n{after}\n```"


def main():
    mcp.run()


if __name__ == "__main__":
    main()
