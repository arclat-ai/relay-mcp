
from mcp_server.engine.base_detector import BaseDetector, Finding, Span


class SequentialToolDetector(BaseDetector):
    """Flags runs of consecutive, data-independent awaited calls that could run
    concurrently via asyncio.gather()."""

    def detect(self, timeline: list[Span]) -> list[Finding]:
        groups: dict = {}
        for s in timeline:
            if s.span_type == "tool_call":
                gid = s.metadata.get("group_id")
                if gid:
                    groups.setdefault(gid, []).append(s)

        findings = []
        for spans in groups.values():
            if len(spans) < 2:
                continue
            spans = sorted(spans, key=lambda s: s.metadata.get("line", 0))
            durations = [s.duration_ms for s in spans]
            first = spans[0]
            last = spans[-1]
            location = f"{first.metadata.get('file')}:{first.metadata.get('line')}-{last.metadata.get('line')}"

            before = "\n".join(s.metadata.get("code", "") for s in spans)
            targets = [", ".join(s.metadata.get("targets", [])) or "_" for s in spans]
            calls = [
                s.metadata.get("call_src", "").strip()[6:].strip()
                if s.metadata.get("call_src", "").strip().startswith("await ")
                else s.metadata.get("call_src", "").strip()
                for s in spans
            ]
            after = f"{', '.join(targets)} = await asyncio.gather(\n    " + ",\n    ".join(calls) + "\n)"

            findings.append(Finding(
                type="sequential_tools",
                severity="high" if len(spans) >= 3 else "medium",
                title="Parallelize independent tool calls",
                description=(
                    f"{len(spans)} consecutive awaited calls are data-independent "
                    f"and can run concurrently with asyncio.gather() instead of one at a time."
                ),
                time_lost_ms=sum(durations) - max(durations),
                location=location,
                rank=0,
                code_before=before,
                code_after=after,
                effort="low",
                impact="high",
            ))
        return findings
