from typing import List
from app.engine.base_detector import BaseDetector, Span, Finding

class BlockingIODetector(BaseDetector):
    def detect(self, timeline: List[Span]) -> List[Finding]:
        findings = []

        for span in timeline:
            if span.span_type in ("db_query", "api_call"):
                is_async = span.metadata.get("async", True)
                if not is_async and span.duration_ms > 100:
                    findings.append(Finding(
                        type="blocking_io",
                        severity="medium",
                        title="Make I/O calls async",
                        description="Synchronous DB and API calls block the event loop. Replace with async equivalents so the agent can handle other work while waiting.",
                        time_lost_ms=span.duration_ms,
                        location=span.name,
                        rank=0,
                        code_before="result = requests.get(url)\ndata = db_session.execute(query)",
                        code_after="async with httpx.AsyncClient() as client:\n    result = await client.get(url)\ndata = await async_session.execute(query)",
                        effort="medium",
                        impact="medium"
                    ))

        return findings
