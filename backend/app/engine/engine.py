from typing import Dict, Any, List
from app.engine.ingester import parse_logs, parse_description
from app.engine.scorer import rank_findings, summarize_audit
from app.engine.detectors.sync_output import SyncOutputDetector
from app.engine.detectors.sequential_tools import SequentialToolDetector
from app.engine.detectors.cache_miss import CacheMissDetector
from app.engine.detectors.blocking_io import BlockingIODetector
from app.engine.detectors.cold_start import ColdStartDetector
from app.engine.detectors.prefetch import PrefetchDetector
from dataclasses import asdict

class AuditResult:
    def __init__(self, bottlenecks: list, summary: dict):
        self.bottlenecks = bottlenecks
        self.summary = summary
        
    def to_dict(self):
        return {
            "bottlenecks": [asdict(b) for b in self.bottlenecks],
            "summary": self.summary
        }

class AuditEngine:
    def run(self, input_type: str, input_data: str) -> AuditResult:
        if input_type == "logs":
            timeline = parse_logs(input_data)
        else:
            timeline = parse_description(input_data)
            
        all_findings = []
        detectors = [
            SyncOutputDetector(),
            SequentialToolDetector(),
            CacheMissDetector(),
            BlockingIODetector(),
            ColdStartDetector(),
            PrefetchDetector()
        ]
        
        for detector in detectors:
            all_findings.extend(detector.detect(timeline))
            
        ranked = rank_findings(all_findings)
        summary = summarize_audit(ranked, timeline)
        
        return AuditResult(bottlenecks=ranked, summary=summary)
