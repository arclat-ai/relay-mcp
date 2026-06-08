from typing import List
from mcp_server.engine.base_detector import BaseDetector, Span, Finding


class CacheMissDetector(BaseDetector):
    def detect(self, timeline: List[Span]) -> List[Finding]:
        findings = []
        call_map = {}

        for span in timeline:
            if span.span_type == "llm_call":
                prompt_hash = span.metadata.get("prompt_hash")
                if prompt_hash:
                    key = (span.name, prompt_hash)
                    if key not in call_map:
                        call_map[key] = []
                    call_map[key].append(span)

        for key, spans in call_map.items():
            count = len(spans)
            if count >= 2:
                avg_duration = sum(s.duration_ms for s in spans) / count
                time_lost = int((count - 1) * avg_duration)
                name = key[0]

                findings.append(Finding(
                    type="cache_miss",
                    severity="medium",
                    title="Add API response caching",
                    description="Cache responses for identical inputs with Redis or an LRU cache. Repeated identical LLM calls pay full latency cost every time.",
                    time_lost_ms=time_lost,
                    location=name,
                    rank=0,
                    code_before="response = await llm.call(prompt)",
                    code_after="cache_key = hashlib.md5(prompt.encode()).hexdigest()\ncached = await redis.get(cache_key)\nif cached:\n    return cached\nresponse = await llm.call(prompt)\nawait redis.set(cache_key, response, ex=3600)",
                    effort="medium",
                    impact="medium"
                ))

        return findings
