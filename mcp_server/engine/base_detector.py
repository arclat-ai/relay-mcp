from dataclasses import dataclass, field
from typing import Dict, Any, List


@dataclass
class Finding:
    type: str
    severity: str
    title: str
    description: str
    time_lost_ms: int
    location: str
    rank: int
    code_before: str
    code_after: str
    effort: str
    impact: str
    occurrences: int = 1
    file: str = ""
    lines: List[int] = field(default_factory=list)


@dataclass
class Span:
    id: str
    name: str
    start_ms: int
    end_ms: int
    duration_ms: int
    span_type: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseDetector:
    def detect(self, timeline: List[Span]) -> List[Finding]:
        raise NotImplementedError
