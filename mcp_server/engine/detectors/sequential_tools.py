from typing import List
from mcp_server.engine.base_detector import BaseDetector, Span, Finding


class SequentialToolDetector(BaseDetector):
    def detect(self, timeline: List[Span]) -> List[Finding]:
        findings = []
        tool_spans = [s for s in timeline if s.span_type == "tool_call"]
        if not tool_spans:
            return findings

        groups, current_group = [], [tool_spans[0]]
        for i in range(1, len(tool_spans)):
            if tool_spans[i].start_ms - tool_spans[i - 1].end_ms < 50:
                current_group.append(tool_spans[i])
            else:
                if len(current_group) >= 2:
                    groups.append(current_group)
                current_group = [tool_spans[i]]
        if len(current_group) >= 2:
            groups.append(current_group)

        for g in groups:
            durations = [s.duration_ms for s in g]
            findings.append(Finding(
                type="sequential_tools",
                severity="high" if len(g) >= 3 else "medium",
                title="Parallelize independent tool calls",
                description="Run independent tool calls concurrently with asyncio.gather() instead of awaiting them one by one.",
                time_lost_ms=sum(durations) - max(durations),
                location=", ".join(s.name for s in g),
                rank=0,
                code_before="result_a = await tool_a()\nresult_b = await tool_b()",
                code_after="result_a, result_b = await asyncio.gather(tool_a(), tool_b())",
                effort="low",
                impact="high",
            ))
        return findings
