from dataclasses import asdict
from datetime import UTC, datetime

from mcp_server.engine.base_detector import Span
from mcp_server.engine.code_parser import CodeParser
from mcp_server.engine.detectors.blocking_io import BlockingIODetector
from mcp_server.engine.detectors.cache_miss import CacheMissDetector
from mcp_server.engine.detectors.cold_start import ColdStartDetector
from mcp_server.engine.detectors.prefetch import PrefetchDetector
from mcp_server.engine.detectors.sequential_tools import SequentialToolDetector
from mcp_server.engine.detectors.sync_output import SyncOutputDetector
from mcp_server.engine.scorer import dedupe_findings, rank_findings, summarize_audit
from mcp_server.engine.verify import verify_findings

SCHEMA_VERSION = "1.1"


class AuditResult:
    def __init__(
        self,
        bottlenecks: list,
        summary: dict,
        target: str = "",
        files_scanned: int = 0,
        def_index: dict | None = None,
    ):
        self.bottlenecks = bottlenecks
        self.summary = summary
        self.target = target
        self.files_scanned = files_scanned
        self.def_index = def_index
        self._verified = None  # cached (findings_with_verdicts, verify_summary)

    def _finding_dict(self, f):
        d = asdict(f)
        # Structured location for dashboard consumption; keep flat fields too.
        d["location"] = {
            "display": f.location,
            "file": f.file,
            "lines": f.lines,
            "occurrences": f.occurrences,
        }
        return d

    def _verify(self):
        """Run the semantic verify pass once and nest each verdict under a
        `verification` key on the finding dict."""
        if self._verified is None:
            raw = [self._finding_dict(b) for b in self.bottlenecks]
            v = verify_findings(raw, self.target or None, def_index=self.def_index)
            annotated = []
            for g in v["findings"]:
                ver_status = g.pop("status", "confirmed")
                ver_reason = g.pop("reason", "")
                ver_impact = g.pop("impact", "medium")
                g["verification"] = {
                    "status": ver_status,
                    "reason": ver_reason,
                    "impact": ver_impact,
                }
                g["impact"] = ver_impact
                annotated.append(g)
            self._verified = (annotated, v["summary"])
        return self._verified

    def to_dict(self):
        findings, verify_summary = self._verify()
        return {
            "schema_version": SCHEMA_VERSION,
            "generated_at": datetime.now(UTC).isoformat(),
            "target": self.target,
            "files_scanned": self.files_scanned,
            "summary": self.summary,
            "verification": verify_summary,
            "findings": findings,
            # Backwards-compatible alias for the current MCP server renderer.
            "bottlenecks": findings,
        }


def get_default_detectors():
    return [
        SyncOutputDetector(),
        SequentialToolDetector(),
        CacheMissDetector(),
        BlockingIODetector(),
        ColdStartDetector(),
        PrefetchDetector(),
    ]


_DETECTORS = get_default_detectors()


class AuditEngine:
    def __init__(self, detectors: list | None = None):
        self.detectors = list(detectors) if detectors is not None else get_default_detectors()

    def run_on_codebase(self, directory: str) -> AuditResult:
        parser = CodeParser()
        timeline: list[Span] = parser.parse_directory(directory)
        all_findings = []
        for detector in self.detectors:
            all_findings.extend(detector.detect(timeline))
        deduped = dedupe_findings(all_findings)
        ranked = rank_findings(deduped)
        summary = summarize_audit(ranked, timeline)
        return AuditResult(
            bottlenecks=ranked,
            summary=summary,
            target=directory,
            files_scanned=getattr(parser, "files_scanned", 0),
            def_index=getattr(parser, "def_index", None),
        )
