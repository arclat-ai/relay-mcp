"""
Arclat MCP Server
Run via: uvx arclat-mcp  (or: python -m mcp_server.server)
"""
import os
from dataclasses import asdict

from mcp.server.fastmcp import FastMCP

from mcp_server.engine.engine import AuditEngine
from mcp_server.usage.tracker import validate_and_check, increment

mcp = FastMCP("arclat")

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
        lines.append(f"\n### {icon} [{f['rank']}] {f['title']}")
        lines.append(f"**Location:** {f['location']}")
        lines.append(f"**Severity:** {f['severity'].upper()}  |  **Time lost:** ~{f['time_lost_ms']}ms")
        lines.append(f"**Fix effort:** {f['effort']}  |  **Impact:** {f['impact']}")
        lines.append(f"\n{f['description']}")
        if f.get("code_before") and f.get("code_after"):
            lines.append(f"\n**Before:**\n```python\n{f['code_before']}\n```")
            lines.append(f"**After:**\n```python\n{f['code_after']}\n```")
    return "\n".join(lines)


@mcp.tool()
def audit_codebase(directory: str, api_key: str = "") -> str:
    """
    Audit an AI agent codebase for latency bottlenecks.
    Reads Python files in the given directory and returns ranked findings with fix recommendations.

    Args:
        directory: Absolute path to the codebase directory to audit.
        api_key: Your Arclat API key (arc_...). Get one at https://arclat.vercel.app
    """
    global _last_result

    # Fall back to env var if not passed directly
    key = api_key or os.getenv("ARCLAT_API_KEY", "")

    allowed, reason = validate_and_check(key)
    if not allowed:
        return f"❌ {reason}"

    result = AuditEngine().run_on_codebase(directory)
    _last_result = result

    increment(key)

    summary = result.summary
    bottlenecks = result.to_dict()["bottlenecks"]

    header = (
        f"## Arclat Audit Report\n"
        f"**{summary['total_bottlenecks']} bottleneck(s) found · "
        f"~{summary['estimated_improvement_pct']}% estimated improvement**\n"
        f"**Top issue:** {summary['top_issue']}\n"
    )

    return header + _format_findings(bottlenecks)


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
