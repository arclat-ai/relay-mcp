
from mcp_server.engine.base_detector import BaseDetector, Finding, Span


class SyncOutputDetector(BaseDetector):
    def detect(self, timeline: list[Span]) -> list[Finding]:
        findings = []
        for span in timeline:
            if span.span_type == "llm_call" and span.duration_ms > 2000:
                if not span.metadata.get("streaming", False):
                    code = span.metadata.get("code", "")
                    unknown = span.metadata.get("streaming_unknown", False)
                    if code.endswith(")"):
                        after = code[:-1] + ", stream=True)"
                    else:
                        after = code + "  # add stream=True"
                    if unknown:
                        desc = ("This LLM call forwards args via **kwargs, so streaming can't be confirmed statically. "
                                "Verify stream=True is set; if not, enabling it cuts time-to-first-token.")
                    else:
                        desc = ("This LLM call waits for the full completion before returning. "
                                "Stream tokens as they are generated with stream=True to cut time-to-first-token.")
                    findings.append(Finding(
                        type="sync_output",
                        severity="medium" if unknown else "high",
                        title="Enable streaming output",
                        description=desc,
                        time_lost_ms=int(span.duration_ms * 0.5),
                        location=span.name,
                        rank=0,
                        code_before=code,
                        code_after=after,
                        effort="low",
                        impact="high",
                    ))
        return findings
