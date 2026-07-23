from typing import List
from mcp_server.engine.base_detector import BaseDetector, Span, Finding


class CacheMissDetector(BaseDetector):
    """Flags LLM calls whose inputs are fully static (every arg is a constant)
    and that appear at 2+ call sites - identical input means an identical,
    cacheable response, yet full latency is paid at every site."""

    def detect(self, timeline: List[Span]) -> List[Finding]:
        findings = []
        call_map: dict = {}
        for span in timeline:
            if span.span_type == "llm_call" and span.metadata.get("prompt_hash"):
                call_map.setdefault(span.metadata["prompt_hash"], []).append(span)
        for spans in call_map.values():
            if len(spans) < 2:
                continue
            avg_dur = sum(s.duration_ms for s in spans) / len(spans)
            first = spans[0]
            findings.append(Finding(
                type="cache_miss",
                severity="medium",
                title="Cache repeated identical LLM calls",
                description=(
                    f"The same fully-static LLM call appears at {len(spans)} call sites. "
                    "Identical input produces an identical response - cache it "
                    "(in-process dict or Redis) instead of paying full latency each time."
                ),
                time_lost_ms=int((len(spans) - 1) * avg_dur),
                location=first.name,
                rank=0,
                code_before=first.metadata.get("code", ""),
                code_after=(
                    "cache_key = hashlib.md5(prompt.encode()).hexdigest()\n"
                    "if cached := await cache.get(cache_key):\n"
                    "    return cached\n"
                    "response = await llm.call(prompt)\n"
                    "await cache.set(cache_key, response, ex=3600)"
                ),
                effort="medium",
                impact="medium",
            ))
        return findings
