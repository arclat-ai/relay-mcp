
from mcp_server.engine.base_detector import BaseDetector, Finding, Span


class PrefetchDetector(BaseDetector):
    """Flags a call pair that independently recurs across many functions -- a
    stable A->B pattern worth speculatively prefetching. Scoped to the
    independent-tool groups so it never fires on unrelated adjacency."""

    def detect(self, timeline: list[Span]) -> list[Finding]:
        groups: dict = {}
        for s in timeline:
            if s.span_type == "tool_call" and s.metadata.get("group_id"):
                groups.setdefault(s.metadata["group_id"], []).append(s)

        pair_hits: dict = {}
        for spans in groups.values():
            spans = sorted(spans, key=lambda s: s.metadata.get("line", 0))
            for a, b in zip(spans, spans[1:], strict=False):
                pair = (a.name, b.name)
                pair_hits.setdefault(pair, []).append(b.duration_ms)

        findings = []
        for pair, durs in pair_hits.items():
            if len(durs) >= 3 and pair[0] != pair[1]:
                findings.append(Finding(
                    type="no_prefetch",
                    severity="low",
                    title="Prefetch predictable next calls",
                    description=f"'{pair[0]}' is repeatedly followed by '{pair[1]}'. Speculatively start the second in the background when the first fires.",
                    time_lost_ms=int(sum(durs) / len(durs)),
                    location=f"{pair[0]} -> {pair[1]}",
                    rank=0,
                    code_before="",
                    code_after="",
                    effort="high",
                    impact="low",
                ))
        return findings
