from typing import List, Dict, Any
from mcp_server.engine.base_detector import Finding, Span


def rank_findings(findings: List[Finding]) -> List[Finding]:
    weight = {"high": 3, "medium": 2, "low": 1}
    sorted_findings = sorted(
        findings,
        key=lambda f: weight.get(f.severity.lower(), 1) * f.time_lost_ms,
        reverse=True,
    )
    for i, f in enumerate(sorted_findings):
        f.rank = i + 1
    return sorted_findings


def summarize_audit(ranked: List[Finding], timeline: List[Span]) -> Dict[str, Any]:
    total_time_lost = sum(f.time_lost_ms for f in ranked)
    total_duration = 0
    if timeline:
        total_duration = max(s.end_ms for s in timeline) - min(s.start_ms for s in timeline)
    pct = min(int((total_time_lost / total_duration) * 100), 80) if total_duration > 0 else 0
    return {
        "total_bottlenecks": len(ranked),
        "estimated_improvement_pct": pct,
        "top_issue": ranked[0].title if ranked else "None",
    }
