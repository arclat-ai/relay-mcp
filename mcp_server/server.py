"""
Relay MCP Server
Run via: uvx --from relay-arclat relay-mcp  (or: python -m mcp_server.server)

Relay is the open-source latency-auditor MCP, a product of the Arclat studio.
"""
import difflib
import json
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path

try:
    from mcp.server.fastmcp import FastMCP
    mcp = FastMCP("relay")
except ImportError:
    class FastMCP:  # type: ignore
        def __init__(self, name: str):
            self.name = name

        def tool(self):
            return lambda fn: fn

        def run(self):
            raise RuntimeError("mcp package is required to run the server. Run: pip install 'mcp>=1.0.0'")

    mcp = FastMCP("relay")

from mcp_server.engine.engine import AuditEngine

DASHBOARD_URL = "https://relay.arclat.com/dashboard"

# Last audit report (dict). Kept in memory and mirrored to disk so
# get_findings / apply_fix / verify_audit survive MCP server restarts.
_STATE_PATH = Path.home() / ".relay" / "last-audit.json"
_last_report: dict | None = None


def _atomic_write(path: Path, content: str, mode: int | None = None) -> None:
    """Atomically write content to a file via a temporary file in the same directory."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if mode is not None and os.name != "nt":
        try:
            os.chmod(path.parent, 0o700)
        except OSError:
            pass
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, prefix=".tmp_relay_")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        if mode is not None and os.name != "nt":
            try:
                os.chmod(tmp_path, mode)
            except OSError:
                pass
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def _save_last(report: dict) -> None:
    global _last_report
    _last_report = report
    try:
        _atomic_write(_STATE_PATH, json.dumps(report), mode=0o600)
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
        return f"**Verified:** ✓ confirmed ({v['impact']} impact) - {v['reason']}"
    return f"**Verified:** ✗ dismissed - {v['reason']}"


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
        lines.append(f"**Fix effort:** {f.get('effort', 'medium')}  |  **Impact:** {f.get('impact', 'medium')}")
        vline = _verification_line(f)
        if vline:
            lines.append(vline)
        lines.append(f"\n{f['description']}")
        if f.get("code_before") and f.get("code_after"):
            lines.append(f"\n**Before:**\n```python\n{f['code_before']}\n```")
            lines.append(f"**After:**\n```python\n{f['code_after']}\n```")
    return "\n".join(lines)


def _write_report(report: dict, directory: str, archive: bool = False) -> Path:
    """
    Persist the audit as a JSON report the Relay dashboard can load.

    Writes relay-report.json into the audited directory.
    If archive is True, also writes an immutable timestamped copy relay-report-<stamp>.json.
    Upload either to https://relay.arclat.com/dashboard.
    """
    report = dict(report)
    report["generator"] = "relay-mcp"
    report["product"] = "relay"

    out_dir = Path(directory)
    if not out_dir.is_dir():
        out_dir = Path.cwd()

    latest = out_dir / "relay-report.json"
    payload = json.dumps(report, indent=2)

    try:
        _atomic_write(latest, payload)
    except OSError:
        pass

    if archive:
        stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        history = out_dir / f"relay-report-{stamp}.json"
        try:
            _atomic_write(history, payload)
        except OSError:
            pass

    return latest


@mcp.tool()
def audit_codebase(directory: str, write_report: bool = True, archive_report: bool = False) -> str:
    """
    Audit an AI agent codebase for latency bottlenecks.
    Reads Python files in the given directory and returns ranked findings with
    fix recommendations. Every finding also carries a verification verdict
    (confirmed / dismissed with a reason) from a semantic second pass.

    Args:
        directory: Absolute path to the codebase directory to audit.
        write_report: Write relay-report.json into the audited directory (default True).
        archive_report: Also write an immutable timestamped copy relay-report-<timestamp>.json (default False).
    """
    if not Path(directory).is_dir():
        return f"❌ Not a directory: `{directory}`. Pass an absolute path to the codebase root."

    result = AuditEngine().run_on_codebase(directory)
    report = result.to_dict()
    _save_last(report)

    if result.files_scanned == 0:
        return (
            f"⚠️ No Python files found under `{directory}` "
            "(venv/tests/examples/docs are skipped). Nothing was audited - "
            "check the path points at the codebase root."
        )

    saved_note = ""
    if write_report:
        report_path = _write_report(report, directory, archive=archive_report)
        saved_note = f"\n_Saved to `{report_path}` - upload it to {DASHBOARD_URL} for the full analytics view._\n"

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
        severity: Filter by severity - 'high', 'medium', or 'low'. Leave blank for all.
        finding_type: Filter by type e.g. 'sequential_tools', 'sync_output'. Leave blank for all.
        status: Filter by verification status - 'confirmed' or 'dismissed'. Leave blank for all.
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
        lines.append(f"- {mark} **[{f['rank']}] {f['title']}** - {ver['reason']}  \n  `{loc_str}`")
    return "\n".join(lines)


def _reindent_replacement(source: str, before: str, after: str) -> tuple[str | None, str | None, str | None]:
    """
    Locate `before` in `source`, handling both exact match and indented function bodies.
    Returns (new_source, actual_before_matched, indented_after_replacement).
    """
    if before in source:
        return source.replace(before, after, 1), before, after

    newline = "\r\n" if "\r\n" in source else "\n"
    source_lines = source.splitlines()
    before_lines = [b.strip() for b in before.splitlines() if b.strip()]
    if not before_lines or len(source_lines) < len(before_lines):
        return None, None, None

    for i in range(len(source_lines) - len(before_lines) + 1):
        candidate_slice = source_lines[i:i + len(before_lines)]
        if all(c.strip() == b for c, b in zip(candidate_slice, before_lines, strict=True)):
            first_line = source_lines[i]
            indent_len = len(first_line) - len(first_line.lstrip())
            indent = first_line[:indent_len]
            actual_before = newline.join(candidate_slice)
            indented_after = newline.join(
                indent + line if line.strip() else "" for line in after.splitlines()
            )
            prefix = newline.join(source_lines[:i]) + (newline if i > 0 else "")
            suffix = (newline if i + len(before_lines) < len(source_lines) else "") + newline.join(
                source_lines[i + len(before_lines):]
            )
            if source.endswith(newline) and not suffix.endswith(newline):
                suffix += newline
            new_source = prefix + indented_after + suffix
            return new_source, actual_before, indented_after

    return None, None, None


def _generate_diff(file_path: str, old_source: str, new_source: str) -> str:
    """Generate a unified diff (diff -u) comparing old and new source."""
    old_lines = old_source.splitlines(keepends=True)
    new_lines = new_source.splitlines(keepends=True)
    file_display = file_path.replace("\\", "/")
    diff = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=f"a/{file_display}",
        tofile=f"b/{file_display}",
    )
    return "".join(diff)


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

    bottlenecks = report.get("bottlenecks", [])
    match = next((b for b in bottlenecks if b["rank"] == finding_rank), None)
    if match is None:
        return f"No finding with rank {finding_rank}. Valid ranks: {[b['rank'] for b in bottlenecks]}"

    if not file_path:
        loc = match.get("location")
        file_path = (loc.get("file") if isinstance(loc, dict) else "") or match.get("file", "")
    if not file_path or not file_path.endswith(".py"):
        return "This finding has no single file location - pass file_path explicitly."

    resolved_file = Path(file_path).resolve()

    # Security check: Ensure file is within target directory if known
    target_dir_str = report.get("target", "")
    if target_dir_str:
        target_dir = Path(target_dir_str).resolve()
        if target_dir.is_dir():
            try:
                resolved_file.relative_to(target_dir)
            except ValueError:
                return (
                    f"Security error: '{file_path}' resolves outside the audited directory "
                    f"'{target_dir}'. Refusing to modify files outside target."
                )

    if not resolved_file.is_file():
        return f"File not found: {file_path}"

    before = match.get("code_before", "")
    after = match.get("code_after", "")

    if not before or not after:
        return f"Finding '{match['title']}' does not have an automated fix. Apply manually:\n{match['description']}"

    try:
        source = resolved_file.read_text(encoding="utf-8")
    except OSError as e:
        return f"Could not read {file_path}: {e}"

    new_source, actual_before, indented_after = _reindent_replacement(source, before, after)
    if new_source is None:
        return (
            f"Could not locate the exact pattern in {file_path}.\n"
            f"Apply manually - replace:\n```python\n{before}\n```\nwith:\n```python\n{after}\n```"
        )

    diff_text = _generate_diff(file_path, source, new_source)

    if dry_run:
        return (
            f"**Dry run - no changes written.**\n\n"
            f"File: `{file_path}`\n\n"
            f"```diff\n{diff_text}\n```\n\n"
            f"Call with `dry_run=False` to apply this change."
        )

    try:
        _atomic_write(resolved_file, new_source)
    except OSError as e:
        return f"Failed to write fix to `{file_path}`: {e}"

    return (
        f"✅ Fix applied to `{file_path}`.\n\n"
        f"```diff\n{diff_text}\n```"
    )


def main():
    mcp.run()


if __name__ == "__main__":
    main()
