from typing import List
from app.engine.base_detector import BaseDetector, Span, Finding

class SyncOutputDetector(BaseDetector):
    def detect(self, timeline: List[Span]) -> List[Finding]:
        findings = []
        for span in timeline:
            if span.span_type == "llm_call" and span.duration_ms > 2000:
                is_streaming = span.metadata.get("streaming", False)
                if not is_streaming:
                    time_lost = int(span.duration_ms * 0.5)
                    findings.append(Finding(
                        type="sync_output",
                        severity="high",
                        title="Enable streaming output",
                        description="Stream tokens as they are generated instead of waiting for the full completion. Use stream=True and process chunks with an async generator.",
                        time_lost_ms=time_lost,
                        location=span.name,
                        rank=0,
                        code_before='''response = client.chat.completions.create(model=model, messages=messages)\noutput = response.choices[0].message.content''',
                        code_after='''async for chunk in client.chat.completions.create(\n    model=model, messages=messages, stream=True\n):\n    delta = chunk.choices[0].delta.content or ""\n    yield delta''',
                        effort="low",
                        impact="high"
                    ))
        return findings
