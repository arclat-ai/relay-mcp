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


@dataclass
class Span:
    id: str
    name: str
    start_ms: int
    end_ms: int
    duration_ms: int
    span_type: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CodeSpan:
    """Represents a detected pattern in source code. Compatible with Span for detectors."""
    id: str
    name: str
    file_path: str
    line_number: int
    span_type: str
    pattern: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    # Synthetic time fields derived from line position for detector compatibility
    start_ms: int = 0
    end_ms: int = 50
    duration_ms: int = 50


class BaseDetector:
    def detect(self, timeline: List[Span]) -> List[Finding]:
        raise NotImplementedError("Subclasses must implement detect")
