from typing import Any

from mcp_server.engine.base_detector import Finding, Span


def _file_of(location: str) -> str:
    """Extract the source file from a finding location, ignoring line/call prefix."""
    if ".py" not in location:
        return location                    # abstract location e.g. 'A -> B'
    loc = location.split("@")[-1]          # strip 'requests.get@' style prefix
    parts = loc.rsplit(":", 1)
    if len(parts) == 2 and any(c.isdigit() for c in parts[1]) and all(c.isdigit() or c == "-" for c in parts[1].strip()):
        return parts[0]
    return loc


def _lines_of(location: str) -> list[int]:
    """Extract line numbers from a location's trailing ':NN' or ':a-b'."""
    if ".py" not in location:
        return []
    parts = location.split("@")[-1].rsplit(":", 1)
    if len(parts) < 2:
        return []
    seg = parts[1].strip()
    if not (any(c.isdigit() for c in seg) and all(c.isdigit() or c == "-" for c in seg)):
        return []
    return [int(n) for n in seg.split("-") if n.isdigit()]


def dedupe_findings(findings: list[Finding]) -> list[Finding]:
    """Collapse same-type findings within the same file into one entry so a
    repeated pattern (e.g. streaming across N provider adapters) reads as a
    single actionable item with an occurrence count."""
    merged: dict = {}
    order: list[tuple] = []
    for f in findings:
        f.file = _file_of(f.location)
        f.lines = _lines_of(f.location)
        key = (f.type, f.file)
        if key not in merged:
            merged[key] = f
            order.append(key)
        else:
            base = merged[key]
            base.occurrences += 1
            base.time_lost_ms += f.time_lost_ms
            base.lines = sorted(set(base.lines + f.lines))
    for key in order:
        f = merged[key]
        if f.occurrences > 1:
            f.location = f"{f.file} ({f.occurrences} occurrences)"
            f.description += f" Found in {f.occurrences} places in this file."
    return [merged[k] for k in order]


def rank_findings(findings: list[Finding]) -> list[Finding]:
    weight = {"high": 3, "medium": 2, "low": 1}
    sorted_findings = sorted(
        findings,
        key=lambda f: weight.get(f.severity.lower(), 1) * f.time_lost_ms,
        reverse=True,
    )
    for i, f in enumerate(sorted_findings):
        f.rank = i + 1
    return sorted_findings


def summarize_audit(ranked: list[Finding], timeline: list[Span]) -> dict[str, Any]:
    # Savings vs. the sequential critical path of the work we actually modeled.
    # This is an internally-consistent estimate, not a codebase-wide guarantee.
    total_time_lost = sum(f.time_lost_ms for f in ranked)
    modeled_duration = sum(s.duration_ms for s in timeline) if timeline else 0
    pct = min(int((total_time_lost / modeled_duration) * 100), 60) if modeled_duration > 0 else 0

    sev_counts = {"high": 0, "medium": 0, "low": 0}
    type_counts: dict[str, int] = {}
    for f in ranked:
        sev_counts[f.severity] = sev_counts.get(f.severity, 0) + 1
        type_counts[f.type] = type_counts.get(f.type, 0) + 1

    return {
        "total_bottlenecks": len(ranked),
        "total_occurrences": sum(f.occurrences for f in ranked),
        "estimated_improvement_pct": pct,
        "total_time_lost_ms": total_time_lost,
        "severity_counts": sev_counts,
        "type_counts": type_counts,
        "top_issue": ranked[0].title if ranked else "None",
    }
