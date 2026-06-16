from typing import List
from mcp_server.engine.base_detector import BaseDetector, Span, Finding


class CacheMissDetector(BaseDetector):
    def detect(self, timeline: List[Span]) -> List[Finding]:
        findings = []
        call_map: dict = {}
        for span in timeline:
            if span.span_type == "llm_call":
                prompt_hash = span.metadata.get("prompt_hash")
                if prompt_hash:
                    call_map.setdefault((span.name, prompt_hash), []).append(span)
        for key, spans in call_map.items():
            if len(spans) >= 2:
                avg_dur = sum(s.duration_ms for s in spans) / len(spans)
                findings.append(Finding(
                    type="cache_miss",
                    severity="medium",
                    title="Add API response caching",
                    description="Cache responses for identical inputs. Repeated identical LLM calls pay full latency every time.",
                    time_lost_ms=int((len(spans) - 1) * avg_dur),
                    location=key[0],
                    rank=0,
                    code_before="response = await llm.call(prompt)",
                    code_after="cache_key = hashlib.md5(prompt.encode()).hexdigest()\nif cached := await redis.get(cache_key):\n    return cached\nresponse = await llm.call(prompt)\nawait redis.set(cache_key, response, ex=3600)",
                    effort="medium",
                    impact="medium",
                ))
        return findings
