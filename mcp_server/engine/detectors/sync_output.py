from typing import List
from mcp_server.engine.base_detector import BaseDetector, Span, Finding


class SyncOutputDetector(BaseDetector):
    def detect(self, timeline: List[Span]) -> List[Finding]:
        findings = []
        for span in timeline:
            if span.span_type == "llm_call" and span.duration_ms > 2000:
                if not span.metadata.get("streaming", False):
                    findings.append(Finding(
                        type="sync_output",
                        severity="high",
                        title="Enable streaming output",
                        description="Stream tokens as they are generated instead of waiting for the full completion. Use stream=True.",
                        time_lost_ms=int(span.duration_ms * 0.5),
                        location=span.name,
                        rank=0,
                        code_before="response = client.chat.completions.create(model=model, messages=messages)",
                        code_after="async for chunk in client.chat.completions.create(model=model, messages=messages, stream=True):\n    yield chunk.choices[0].delta.content or \"\"",
                        effort="low",
                        impact="high",
                    ))
        return findings
