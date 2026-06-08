from typing import List, Dict, Any
from mcp_server.engine.base_detector import Finding, Span


def rank_findings(findings: List[Finding]) -> List[Finding]:
    severity_weight = {"high": 3, "medium": 2, "low": 1}

    sorted_findings = sorted(
        findings,
        key=lambda f: severity_weight.get(f.severity.lower(), 1) * f.time_lost_ms,
        reverse=True
    )

    for i, finding in enumerate(sorted_findings):
        finding.rank = i + 1

    return sorted_findings


def summarize_audit(ranked_findings: List[Finding], timeline: List[Span]) -> Dict[str, Any]:
    total_bottlenecks = len(ranked_findings)
    total_time_lost = sum(f.time_lost_ms for f in ranked_findings)

    total_duration = 0
    if timeline:
        min_start = min(s.start_ms for s in timeline)
        max_end = max(s.end_ms for s in timeline)
        total_duration = max_end - min_start

    estimated_improvement_pct = 0
    if total_duration > 0:
        estimated_improvement_pct = int((total_time_lost / total_duration) * 100)

    estimated_improvement_pct = min(estimated_improvement_pct, 80)
    top_issue = ranked_findings[0].title if ranked_findings else "None"

    return {
        "total_bottlenecks": total_bottlenecks,
        "estimated_improvement_pct": estimated_improvement_pct,
        "top_issue": top_issue
    }
