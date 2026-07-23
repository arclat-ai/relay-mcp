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
from mcp_server.usage.tracker import validate_and_check, increment, get_usage

mcp = FastMCP("relay")

DASHBOARD_URL = "https://relay.arclat.com/dashboard"

# Last audit report (dict). Kept in memory and mirrored to disk so
# get_findings / apply_fix / verify_audit survive MCP server restarts.
_STATE_PATH = Path.home() / ".relay" / "last-audit.json"
_last_report: dict | None = None


def _save_last(report: dict) -> None:
    global _last_report
    _last_report = report
    try:
        _STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        _STATE_PATH.write_text(json.dumps(report), encoding="utf-8")
    except OSError:
        pass


def _get_last() -> dict | None:
    global _last_report
    if _last_report is not None:
        return _last_report
    try:
        _last_report = json.loads(_STATE_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return _last_report


def _severity_icon(s: str) -> str:
    return {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(s.lower(), "⚪")


def _verification_line(f: dict) -> str:
    v = f.get("verification")
    if not v:
        return ""
    if v["status"] == "confirmed":
        return f"**Verified:** ✓ confirmed ({v['impact']} impact) — {v['reason']}"
    return f"**Verified:** ✗ dismissed — {v['reason']}"


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
        vline = _verification_line(f)
        if vline:
            lines.append(vline)
        lines.append(f"\n{f['description']}")
        if f.get("code_before") and f.get("code_after"):
            lines.append(f"\n**Before:**\n```python\n{f['code_before']}\n```")
            lines.append(f"**After:**\n```python\n{f['code_after']}\n```")
    return "\n".join(lines)


def _write_report(report: dict, directory: str) -> Path:
    """
    Persist the audit as a JSON report the Relay dashboard can load.

    Writes two files into the audited directory:
      - relay-report.json                      (always the latest run)
      - relay-report-<UTC timestamp>.json      (an immutable history copy)
    Upload either to https://relay.arclat.com/dashboard.
    """
    report = dict(report)
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
def audit_codebase(directory: str, api_key: str = "", write_report: bool = True) -> str:
    """
    Audit an AI agent codebase for latency bottlenecks.
    Reads Python files in the given directory and returns ranked findings with
    fix recommendations. Every finding also carries a verification verdict
    (confirmed / dismissed with a reason) from a semantic second pass.

    Args:
        directory: Absolute path to the codebase directory to audit.
        api_key: Your Relay API key (rly_...). Get one at https://relay.arclat.com
        write_report: Write relay-report.json into the audited directory (default True).
    """
    # Fall back to env var if not passed directly
    key = api_key or os.getenv("RELAY_API_KEY", "") or os.getenv("ARCLAT_API_KEY", "")

    allowed, reason = validate_and_check(key)
    if not allowed:
        return f"❌ {reason}"

    if not Path(directory).is_dir():
        return f"❌ Not a directory: `{directory}`. Pass an absolute path to the codebase root."

    result = AuditEngine().run_on_codebase(directory)
    report = result.to_dict()
    _save_last(report)

    increment(key)

    if result.files_scanned == 0:
        return (
            f"⚠️ No Python files found under `{directory}` "
            "(venv/tests/examples/docs are skipped). Nothing was audited — "
            "check the path points at the codebase root."
        )

    saved_note = ""
    if write_report:
        report_path = _write_report(report, directory)
        saved_note = f"\n_Saved to `{report_path}` — upload it to {DASHBOARD_URL} for the full analytics view._\n"

    summary = report["summary"]
    verification = report["verification"]
    bottlenecks = report["bottlenecks"]

    header = (
        f"## Relay Audit Report\n"
        f"**{summary['total_bottlenecks']} bottleneck(s) found · "
        f"~{summary['estimated_improvement_pct']}% estimated improvement**\n"
        f"**Verified:** {verification['confirmed']} confirmed "
        f"({verification['confirmed_high_impact']} high-impact) · "
        f"{verification['dismissed']} dismissed as likely false positives\n"
        f"**Top issue:** {summary['top_issue']}\n"
        f"{saved_note}"
    )

    return header + _format_findings(bottlenecks)


@mcp.tool()
def get_findings(severity: str = "", finding_type: str = "", status: str = "") -> str:
    """
    Return findings from the last audit, optionally filtered.

    Args:
        severity: Filter by severity — 'high', 'medium', or 'low'. Leave blank for all.
        finding_type: Filter by type e.g. 'sequential_tools', 'sync_output'. Leave blank for all.
        status: Filter by verification status — 'confirmed' or 'dismissed'. Leave blank for all.
    """
    report = _get_last()
    if report is None:
        return "No audit has been run yet. Call audit_codebase first."

    bottlenecks = report["bottlenecks"]
    if severity:
        bottlenecks = [b for b in bottlenecks if b["severity"].lower() == severity.lower()]
    if finding_type:
        bottlenecks = [b for b in bottlenecks if b["type"].lower() == finding_type.lower()]
    if status:
        bottlenecks = [b for b in bottlenecks
                       if b.get("verification", {}).get("status", "") == status.lower()]

    if not bottlenecks:
        types = sorted({b["type"] for b in report["bottlenecks"]})
        return ("No findings match the given filters. "
                f"Types present in the last audit: {', '.join(types) or 'none'}.")
    return _format_findings(bottlenecks)


@mcp.tool()
def verify_audit() -> str:
    """
    Show the verification verdicts for the last audit: which findings the
    semantic pass confirmed as real latency gaps and which it dismissed as
    likely false positives (with the reason for each).
    """
    report = _get_last()
    if report is None:
        return "No audit has been run yet. Call audit_codebase first."

    v = report.get("verification", {})
    lines = [
        "## Relay Verification",
        f"**{v.get('confirmed', 0)} confirmed** ({v.get('confirmed_high_impact', 0)} high-impact) · "
        f"{v.get('dismissed', 0)} dismissed of {v.get('flagged', 0)} flagged\n",
    ]
    for f in report["bottlenecks"]:
        ver = f.get("verification")
        if not ver:
            continue
        loc = f["location"]
        loc_str = loc["display"] if isinstance(loc, dict) else loc
        mark = "✓" if ver["status"] == "confirmed" else "✗"
        lines.append(f"- {mark} **[{f['rank']}] {f['title']}** — {ver['reason']}  \n  `{loc_str}`")
    return "\n".join(lines)


@mcp.tool()
def usage_status(api_key: str = "") -> str:
    """
    Show your Relay plan and how many audits you have used / have left this month.

    Args:
        api_key: Your Relay API key. Falls back to RELAY_API_KEY env var.
    """
    key = api_key or os.getenv("RELAY_API_KEY", "") or os.getenv("ARCLAT_API_KEY", "")
    if not key or not (key.startswith("rly_") or key.startswith("arc_")):
        return "❌ Invalid API key format. Get your key at https://relay.arclat.com"
    u = get_usage(key)
    if u["plan"] == "free":
        return (
            f"**Plan:** free · **Month:** {u['month']}\n"
            f"**Audits used:** {u['count']}/{u['limit']} · **Remaining:** {u['remaining']}\n"
            f"Upgrade for unlimited audits at https://relay.arclat.com"
        )
    return f"**Plan:** {u['plan']} (unlimited) · **Month:** {u['month']} · **Audits used:** {u['count']}"


@mcp.tool()
def apply_fix(finding_rank: int, file_path: str = "", dry_run: bool = True) -> str:
    """
    Apply a fix recommendation from the last audit to a file.

    Args:
        finding_rank: Rank number of the finding to fix (from audit_codebase output).
        file_path: File to modify. Defaults to the file the finding points at.
        dry_run: If True (default), show what would change without writing. Set to False to apply.
    """
    report = _get_last()
    if report is None:
        return "No audit has been run yet. Call audit_codebase first."

    bottlenecks = report["bottlenecks"]
    match = next((b for b in bottlenecks if b["rank"] == finding_rank), None)
    if match is None:
        return f"No finding with rank {finding_rank}. Valid ranks: {[b['rank'] for b in bottlenecks]}"

    if not file_path:
        loc = match.get("location")
        file_path = (loc.get("file") if isinstance(loc, dict) else "") or match.get("file", "")
    if not file_path or not file_path.endswith(".py"):
        return "This finding has no single file location — pass file_path explicitly."

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
