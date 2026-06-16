from typing import List
from mcp_server.engine.base_detector import BaseDetector, Span, Finding


class ColdStartDetector(BaseDetector):
    def detect(self, timeline: List[Span]) -> List[Finding]:
        agent_loops = [s for s in timeline if s.span_type == "agent_loop"]
        if not agent_loops:
            return []
        first = agent_loops[0]
        if first.duration_ms > 500 and any(kw in first.name.lower() for kw in ("init", "setup", "connect")):
            return [Finding(
                type="cold_start",
                severity="low",
                title="Implement connection pooling and warm starts",
                description="Pre-initialize model clients, DB connections, and HTTP sessions at startup instead of per-request.",
                time_lost_ms=first.duration_ms - 50,
                location=first.name,
                rank=0,
                code_before="",
                code_after="",
                effort="medium",
                impact="low",
            )]
        return []
