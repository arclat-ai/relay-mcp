from dataclasses import asdict
from datetime import datetime, timezone
from typing import List

from mcp_server.engine.base_detector import Span
from mcp_server.engine.code_parser import CodeParser
from mcp_server.engine.scorer import rank_findings, summarize_audit, dedupe_findings
from mcp_server.engine.detectors.sync_output import SyncOutputDetector
from mcp_server.engine.detectors.sequential_tools import SequentialToolDetector
from mcp_server.engine.detectors.cache_miss import CacheMissDetector
from mcp_server.engine.detectors.blocking_io import BlockingIODetector
from mcp_server.engine.detectors.cold_start import ColdStartDetector
from mcp_server.engine.detectors.prefetch import PrefetchDetector


SCHEMA_VERSION = "1.0"


class AuditResult:
    def __init__(self, bottlenecks: list, summary: dict, target: str = "", files_scanned: int = 0):
        self.bottlenecks = bottlenecks
        self.summary = summary
        self.target = target
        self.files_scanned = files_scanned

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

    def to_dict(self):
        return {
            "schema_version": SCHEMA_VERSION,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "target": self.target,
            "files_scanned": self.files_scanned,
            "summary": self.summary,
            "findings": [self._finding_dict(b) for b in self.bottlenecks],
            # Backwards-compatible alias for the current MCP server renderer.
            "bottlenecks": [self._finding_dict(b) for b in self.bottlenecks],
        }


_DETECTORS = [
    SyncOutputDetector(),
    SequentialToolDetector(),
    CacheMissDetector(),
    BlockingIODetector(),
    ColdStartDetector(),
    PrefetchDetector(),
]


class AuditEngine:
    def run_on_codebase(self, directory: str) -> AuditResult:
        parser = CodeParser()
        timeline: List[Span] = parser.parse_directory(directory)
        all_findings = []
        for detector in _DETECTORS:
            all_findings.extend(detector.detect(timeline))
        deduped = dedupe_findings(all_findings)
        ranked = rank_findings(deduped)
        summary = summarize_audit(ranked, timeline)
        return AuditResult(
            bottlenecks=ranked,
            summary=summary,
            target=directory,
            files_scanned=getattr(parser, "files_scanned", 0),
        )
