from dataclasses import asdict
from mcp_server.engine.code_parser import CodeParser
from mcp_server.engine.scorer import rank_findings, summarize_audit
from mcp_server.engine.detectors.sync_output import SyncOutputDetector
from mcp_server.engine.detectors.sequential_tools import SequentialToolDetector
from mcp_server.engine.detectors.cache_miss import CacheMissDetector
from mcp_server.engine.detectors.blocking_io import BlockingIODetector
from mcp_server.engine.detectors.cold_start import ColdStartDetector
from mcp_server.engine.detectors.prefetch import PrefetchDetector


class AuditResult:
    def __init__(self, bottlenecks: list, summary: dict):
        self.bottlenecks = bottlenecks
        self.summary = summary

    def to_dict(self):
        return {
            "bottlenecks": [asdict(b) for b in self.bottlenecks],
            "summary": self.summary,
        }


class AuditEngine:
    def __init__(self):
        self._detectors = [
            SyncOutputDetector(),
            SequentialToolDetector(),
            CacheMissDetector(),
            BlockingIODetector(),
            ColdStartDetector(),
            PrefetchDetector(),
        ]

    def run_on_codebase(self, directory: str) -> AuditResult:
        parser = CodeParser()
        spans = parser.parse_directory(directory)

        all_findings = []
        for detector in self._detectors:
            all_findings.extend(detector.detect(spans))

        ranked = rank_findings(all_findings)
        summary = summarize_audit(ranked, spans)
        return AuditResult(bottlenecks=ranked, summary=summary)
