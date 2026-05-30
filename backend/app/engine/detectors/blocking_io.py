from typing import List
from app.engine.base_detector import BaseDetector, Span, Finding

class BlockingIODetector(BaseDetector):
    def detect(self, timeline: List[Span]) -> List[Finding]:
        findings = []
        
        agent_loops = [s for s in timeline if s.span_type == "agent_loop"]
        if not agent_loops:
            # Fallback if no explicit agent_loop is defined: just check db/api calls
            agent_loops = [Span(id="dummy", name="global", start_ms=0, end_ms=10**9, duration_ms=0, span_type="agent_loop")]

        for loop in agent_loops:
            # Find DB/API calls completely contained within this agent_loop
            for span in timeline:
                if span.span_type in ("db_query", "api_call"):
                    if span.start_ms >= loop.start_ms and span.end_ms <= loop.end_ms:
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
