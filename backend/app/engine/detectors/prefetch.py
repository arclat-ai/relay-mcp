from typing import List
from app.engine.base_detector import BaseDetector, Span, Finding

class PrefetchDetector(BaseDetector):
    def detect(self, timeline: List[Span]) -> List[Finding]:
        findings = []
        
        tool_spans = [s for s in timeline if s.span_type == "tool_call"]
        if len(tool_spans) < 2:
            return findings

        pairs_count = {}
        pair_duration = {}
        
        for i in range(len(tool_spans) - 1):
            pair = (tool_spans[i].name, tool_spans[i+1].name)
            
            # Simple sequential check
            if tool_spans[i+1].start_ms >= tool_spans[i].start_ms:
                if pair not in pairs_count:
                    pairs_count[pair] = 0
                    pair_duration[pair] = []
                    
                pairs_count[pair] += 1
                pair_duration[pair].append(tool_spans[i+1].duration_ms)
                
        for pair, count in pairs_count.items():
            if count >= 3:
                avg_duration = int(sum(pair_duration[pair]) / len(pair_duration[pair]))
                findings.append(Finding(
                    type="no_prefetch",
                    severity="low",
                    title="Prefetch predictable next calls",
                    description="When Tool A is called, speculatively begin Tool B in the background - historical patterns show they always run together.",
                    time_lost_ms=avg_duration,
                    location=f"{pair[0]} -> {pair[1]}",
                    rank=0,
                    code_before="",
                    code_after="",
                    effort="high",
                    impact="low"
                ))
                
        return findings
