"""Arclat MCP Server — exposes audit_codebase, get_findings, apply_fix."""

import difflib
import sys
from dataclasses import asdict
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from mcp_server.engine.engine import AuditEngine, AuditResult
from mcp_server.usage.tracker import UsageTracker

server = Server("arclat")
tracker = UsageTracker()

# In-memory cache of last audit result (per server session)
_last_result: AuditResult | None = None
_last_directory: str | None = None


# ── Tool definitions ────────────────────────────────────────────────────────

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="audit_codebase",
            description=(
                "Audits an AI agent codebase for latency bottlenecks. "
                "Reads Python files in the given directory and returns ranked findings."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "Absolute path to the codebase directory to audit.",
                    },
                    "api_key": {
                        "type": "string",
                        "description": "Arclat API key for usage tracking.",
                    },
                },
                "required": ["directory", "api_key"],
            },
        ),
        Tool(
            name="get_findings",
            description=(
                "Returns findings from the last audit, optionally filtered by severity or type."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "severity": {
                        "type": "string",
                        "enum": ["high", "medium", "low"],
                        "description": "Filter findings by severity.",
                    },
                    "finding_type": {
                        "type": "string",
                        "description": "Filter by bottleneck type (e.g. sequential_tools, sync_output).",
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="apply_fix",
            description=(
                "Applies a fix recommendation to the codebase file. "
                "Defaults to dry_run=true — shows a diff without changing any files."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to modify.",
                    },
                    "finding_id": {
                        "type": "string",
                        "description": "Rank of the finding to fix (1-based integer as string).",
                    },
                    "dry_run": {
                        "type": "boolean",
                        "description": "If true (default), show diff without applying.",
                        "default": True,
                    },
                },
                "required": ["file_path", "finding_id"],
            },
        ),
    ]


# ── Tool handlers ───────────────────────────────────────────────────────────

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "audit_codebase":
        return await _audit_codebase(arguments)
    if name == "get_findings":
        return await _get_findings(arguments)
    if name == "apply_fix":
        return await _apply_fix(arguments)
    return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def _audit_codebase(args: dict) -> list[TextContent]:
    global _last_result, _last_directory

    directory = args.get("directory", "")
    api_key = args.get("api_key", "")

    if not Path(directory).is_dir():
        return [TextContent(type="text", text=f"❌ Directory not found: {directory}")]

    user = tracker.validate_key(api_key)
    if user is None:
        return [TextContent(type="text", text="❌ Invalid API key. Get one free at arclat.com")]

    if not tracker.check_limit(api_key):
        usage = tracker.get_usage(api_key)
        return [TextContent(type="text", text=(
            f"❌ Monthly audit limit reached ({usage['count']}/{usage['limit']} audits used). "
            f"Resets {usage['resets_at'][:10]}. Upgrade to Pro at arclat.com for unlimited audits."
        ))]

    engine = AuditEngine()
    result = engine.run_on_codebase(directory)
    tracker.increment(api_key)

    _last_result = result
    _last_directory = directory

    return [TextContent(type="text", text=_format_audit_report(result, directory))]


async def _get_findings(args: dict) -> list[TextContent]:
    if _last_result is None:
        return [TextContent(type="text", text="No audit has been run yet. Use audit_codebase first.")]

    findings = _last_result.bottlenecks
    severity_filter = args.get("severity")
    type_filter = args.get("finding_type")

    if severity_filter:
        findings = [f for f in findings if f.severity.lower() == severity_filter.lower()]
    if type_filter:
        findings = [f for f in findings if f.type.lower() == type_filter.lower()]

    if not findings:
        return [TextContent(type="text", text="No findings match the given filters.")]

    lines = [f"## Filtered Findings ({len(findings)} total)\n"]
    for f in findings:
        lines.append(_format_finding(f))

    return [TextContent(type="text", text="\n".join(lines))]


async def _apply_fix(args: dict) -> list[TextContent]:
    if _last_result is None:
        return [TextContent(type="text", text="No audit has been run yet. Use audit_codebase first.")]

    file_path = args.get("file_path", "")
    finding_id = args.get("finding_id", "")
    dry_run = args.get("dry_run", True)

    try:
        rank = int(finding_id)
    except (ValueError, TypeError):
        return [TextContent(type="text", text="finding_id must be the rank number (e.g. '1')")]

    finding = next((f for f in _last_result.bottlenecks if f.rank == rank), None)
    if finding is None:
        return [TextContent(type="text", text=f"No finding with rank {rank} found.")]

    if not finding.code_before or not finding.code_after:
        return [TextContent(type="text", text=(
            f"Finding '{finding.title}' does not have an automated fix available. "
            f"Apply manually: {finding.description}"
        ))]

    try:
        with open(file_path, "r", encoding="utf-8") as fh:
            original = fh.read()
    except OSError as e:
        return [TextContent(type="text", text=f"Cannot read file: {e}")]

    if finding.code_before not in original:
        return [TextContent(type="text", text=(
            f"Could not find the exact pattern to replace in {file_path}.\n"
            f"Apply manually:\n\n**Before:**\n```python\n{finding.code_before}\n```\n\n"
            f"**After:**\n```python\n{finding.code_after}\n```"
        ))]

    fixed = original.replace(finding.code_before, finding.code_after, 1)

    diff_lines = list(difflib.unified_diff(
        original.splitlines(keepends=True),
        fixed.splitlines(keepends=True),
        fromfile=f"a/{file_path}",
        tofile=f"b/{file_path}",
        lineterm="",
    ))
    diff_str = "".join(diff_lines)

    if dry_run:
        return [TextContent(type="text", text=(
            f"**Dry run** — no files changed.\n\n"
            f"**Fix:** {finding.title}\n\n"
            f"```diff\n{diff_str}\n```\n\n"
            f"Run again with `dry_run: false` to apply."
        ))]

    with open(file_path, "w", encoding="utf-8") as fh:
        fh.write(fixed)

    return [TextContent(type="text", text=(
        f"✅ Applied fix: **{finding.title}**\n\n"
        f"```diff\n{diff_str}\n```"
    ))]


# ── Formatting helpers ──────────────────────────────────────────────────────

_SEVERITY_EMOJI = {"high": "🔴", "medium": "🟡", "low": "🟢"}


def _format_finding(f) -> str:
    emoji = _SEVERITY_EMOJI.get(f.severity.lower(), "⚪")
    lines = [
        f"### {emoji} [#{f.rank}] {f.title}",
        f"**Severity:** {f.severity.capitalize()}  |  **Time lost:** ~{f.time_lost_ms}ms  |  **Effort:** {f.effort}",
        f"**Location:** `{f.location}`",
        f"**Issue:** {f.description}",
    ]
    if f.code_before:
        lines += [
            "\n**Before:**",
            f"```python\n{f.code_before}\n```",
            "**After:**",
            f"```python\n{f.code_after}\n```",
        ]
    return "\n".join(lines) + "\n"


def _format_audit_report(result: AuditResult, directory: str) -> str:
    s = result.summary
    header = (
        f"## Arclat Audit Report\n"
        f"**Directory:** `{directory}`\n"
        f"**{s['total_bottlenecks']} bottleneck(s) found · "
        f"~{s['estimated_improvement_pct']}% estimated improvement**\n\n"
    )
    if not result.bottlenecks:
        return header + "✅ No latency bottlenecks detected."

    findings_text = "\n".join(_format_finding(f) for f in result.bottlenecks)
    return header + findings_text


# ── Entry point ─────────────────────────────────────────────────────────────

def main():
    import asyncio
    asyncio.run(stdio_server(server))


if __name__ == "__main__":
    main()
