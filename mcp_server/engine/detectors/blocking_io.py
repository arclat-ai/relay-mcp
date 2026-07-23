from typing import List
from mcp_server.engine.base_detector import BaseDetector, Span, Finding

_KIND_FIX = {
    "http": ("await client.get(...)  # use httpx.AsyncClient",
             "Synchronous HTTP blocks the event loop, stalling all concurrent "
             "tasks. Replace with httpx.AsyncClient."),
    "db": ("await async_session.execute(query)",
           "Synchronous DB access blocks the event loop, stalling all concurrent "
           "tasks. Use an async driver (asyncpg, aiosqlite, SQLAlchemy async)."),
    "sleep": ("await asyncio.sleep(...)",
              "time.sleep() inside an async function freezes the entire event "
              "loop — every concurrent task stalls. Use await asyncio.sleep()."),
    "subprocess": ("proc = await asyncio.create_subprocess_exec(...)\nout, _ = await proc.communicate()",
                   "A blocking subprocess call inside an async function stalls the "
                   "event loop until the child exits. Use asyncio.create_subprocess_exec."),
}


class BlockingIODetector(BaseDetector):
    def detect(self, timeline: List[Span]) -> List[Finding]:
        findings = []
        for span in timeline:
            if span.span_type in ("db_query", "api_call"):
                if not span.metadata.get("async", True) and span.duration_ms > 100:
                    code = span.metadata.get("code", "")
                    kind = span.metadata.get("kind") or ("http" if span.span_type == "api_call" else "db")
                    after, desc = _KIND_FIX.get(kind, _KIND_FIX["http"])
                    in_async = span.metadata.get("in_async", False)
                    findings.append(Finding(
                        type="blocking_io",
                        severity="high" if in_async else "medium",
                        title="Make I/O calls async" if kind in ("http", "db")
                              else ("Replace time.sleep in async code" if kind == "sleep"
                                    else "Make subprocess calls async"),
                        description=desc,
                        time_lost_ms=span.duration_ms,
                        location=span.name,
                        rank=0,
                        code_before=code,
                        code_after=after,
                        effort="medium",
                        impact="high" if in_async else "medium",
                    ))
        return findings
