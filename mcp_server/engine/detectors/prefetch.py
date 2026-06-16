from typing import List
from mcp_server.engine.base_detector import BaseDetector, Span, Finding


class PrefetchDetector(BaseDetector):
    def detect(self, timeline: List[Span]) -> List[Finding]:
        findings = []
        tool_spans = [s for s in timeline if s.span_type == "tool_call"]
        if len(tool_spans) < 2:
            return findings
        pairs_count: dict = {}
        pair_duration: dict = {}
        for i in range(len(tool_spans) - 1):
            pair = (tool_spans[i].name, tool_spans[i + 1].name)
            if tool_spans[i + 1].start_ms >= tool_spans[i].start_ms:
                pairs_count[pair] = pairs_count.get(pair, 0) + 1
                pair_duration.setdefault(pair, []).append(tool_spans[i + 1].duration_ms)
        for pair, count in pairs_count.items():
            if count >= 3:
                avg = int(sum(pair_duration[pair]) / len(pair_duration[pair]))
                findings.append(Finding(
                    type="no_prefetch",
                    severity="low",
                    title="Prefetch predictable next calls",
                    description="When Tool A is called, speculatively begin Tool B in background — they always run together.",
                    time_lost_ms=avg,
                    location=f"{pair[0]} -> {pair[1]}",
                    rank=0,
                    code_before="",
                    code_after="",
                    effort="high",
                    impact="low",
                ))
        return findings
