from typing import List
from mcp_server.engine.base_detector import BaseDetector, Span, Finding


class ColdStartDetector(BaseDetector):
    """Flags API clients constructed inside per-request functions. Each
    construction pays connection/TLS setup that should happen once at startup."""

    def detect(self, timeline: List[Span]) -> List[Finding]:
        findings = []
        for span in timeline:
            if span.span_type != "client_init":
                continue
            ctor = span.metadata.get("ctor", "client")
            func = span.metadata.get("func", "this function")
            code = span.metadata.get("code", "")
            findings.append(Finding(
                type="cold_start",
                severity="medium",
                title="Reuse API clients across requests",
                description=(
                    f"`{ctor}(...)` is constructed inside `{func}()`, so every call "
                    "pays client setup (TLS handshake, connection pool creation). "
                    "Build the client once at startup (module level, lifespan hook, "
                    "or __init__) and reuse it."
                ),
                time_lost_ms=span.duration_ms,
                location=span.name,
                rank=0,
                code_before=code,
                code_after=f"# at startup / __init__:\nself.client = {code}\n# in {func}(): reuse self.client",
                effort="low",
                impact="medium",
            ))
        return findings
