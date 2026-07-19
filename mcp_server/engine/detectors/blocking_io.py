from typing import List
from mcp_server.engine.base_detector import BaseDetector, Span, Finding


class BlockingIODetector(BaseDetector):
    def detect(self, timeline: List[Span]) -> List[Finding]:
        findings = []
        for span in timeline:
            if span.span_type in ("db_query", "api_call"):
                if not span.metadata.get("async", True) and span.duration_ms > 100:
                    code = span.metadata.get("code", "")
                    is_http = span.span_type == "api_call"
                    after = ("await client.get(...)  # use httpx.AsyncClient"
                             if is_http else "await async_session.execute(query)")
                    findings.append(Finding(
                        type="blocking_io",
                        severity="medium",
                        title="Make I/O calls async",
                        description="Synchronous I/O blocks the event loop, stalling all concurrent tasks. Replace with an async equivalent (httpx.AsyncClient / async DB driver).",
                        time_lost_ms=span.duration_ms,
                        location=span.name,
                        rank=0,
                        code_before=code,
                        code_after=after,
                        effort="medium",
                        impact="medium",
                    ))
        return findings
