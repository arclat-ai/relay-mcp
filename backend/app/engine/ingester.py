import json
import logging
from typing import List, Dict, Any
from app.engine.base_detector import Span

logger = logging.getLogger(__name__)

def parse_logs(raw_json: str) -> List[Span]:
    try:
        data = json.loads(raw_json)
        spans_data = data.get("spans", [])
        
        timeline = []
        for span in spans_data:
            start_ms = span.get("start_ms", 0)
            end_ms = span.get("end_ms", 0)
            duration_ms = end_ms - start_ms
            
            timeline.append(Span(
                id=span.get("id", ""),
                name=span.get("name", ""),
                start_ms=start_ms,
                end_ms=end_ms,
                duration_ms=duration_ms,
                span_type=span.get("span_type", "other"),
                metadata=span.get("metadata", {})
            ))
            
        return sorted(timeline, key=lambda s: s.start_ms)
    except json.JSONDecodeError as e:
        logger.warning("Failed to parse log input as JSON: %s", e)
        return []

def parse_description(text: str) -> List[Span]:
    # Future implementation for plain text description
    return []
