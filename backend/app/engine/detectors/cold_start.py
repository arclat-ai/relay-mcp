from typing import List
from app.engine.base_detector import BaseDetector, Span, Finding

class ColdStartDetector(BaseDetector):
    def detect(self, timeline: List[Span]) -> List[Finding]:
        findings = []
        
        agent_loops = [s for s in timeline if s.span_type == "agent_loop"]
        if not agent_loops:
            return findings
            
        first_loop = agent_loops[0]
        name_lower = first_loop.name.lower()
        
        if first_loop.duration_ms > 500 and any(kw in name_lower for kw in ['init', 'setup', 'connect']):
            findings.append(Finding(
                type="cold_start",
                severity="low",
                title="Implement connection pooling and warm starts",
                description="Pre-initialize model clients, DB connections, and HTTP sessions at application startup instead of per-request.",
                time_lost_ms=first_loop.duration_ms - 50,
                location=first_loop.name,
                rank=0,
                code_before="",
                code_after="",
                effort="medium",
                impact="low"
            ))
            
        return findings
