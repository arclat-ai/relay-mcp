import json
import logging
from typing import List
from app.engine.base_detector import Span

logger = logging.getLogger(__name__)


def _build_timeline(spans_data: list) -> list[Span]:
    """Convert a list of raw span dicts into sorted Span objects."""
    timeline = []
    for span in spans_data:
        start_ms = span.get("start_ms", 0)
        end_ms = span.get("end_ms", 0)
        timeline.append(Span(
            id=str(span.get("id", "")),
            name=str(span.get("name", "")),
            start_ms=int(start_ms),
            end_ms=int(end_ms),
            duration_ms=int(end_ms) - int(start_ms),
            span_type=str(span.get("span_type", "other")),
            metadata=span.get("metadata", {}),
        ))
    return sorted(timeline, key=lambda s: s.start_ms)


def parse_logs(raw_json: str) -> List[Span]:
    """
    Parse raw log JSON into a timeline of Spans.

    Strategy:
    1. Try to parse as our native format {"spans": [...]}.
    2. If that yields zero spans, call the LLM normalizer to convert arbitrary
       tracing formats (OpenTelemetry, LangSmith, Datadog, etc.) into our schema.
    3. Return an empty list if everything fails.
    """
    # ── step 1: native parse ─────────────────────────────────────────────────
    try:
        data = json.loads(raw_json)
        spans_data = data.get("spans", []) if isinstance(data, dict) else []
        timeline = _build_timeline(spans_data)
        if timeline:
            logger.info("Native parse succeeded: %d spans", len(timeline))
            return timeline
    except json.JSONDecodeError as exc:
        logger.warning("JSON decode failed: %s", exc)
        return []

    # ── step 2: LLM normalizer fallback ─────────────────────────────────────
    logger.info("Native parse yielded 0 spans — trying LLM normalizer")
    try:
        from app.engine.normalizer import normalize_to_spans  # lazy import avoids startup error when key is missing

        normalised = normalize_to_spans(raw_json)
        data = json.loads(normalised)
        spans_data = data.get("spans", []) if isinstance(data, dict) else []
        timeline = _build_timeline(spans_data)
        logger.info("LLM normalizer produced %d spans", len(timeline))
        return timeline
    except RuntimeError as exc:
        # API key not configured — log clearly and return empty
        logger.warning("LLM normalizer unavailable: %s", exc)
    except Exception as exc:
        logger.warning("LLM normalizer failed: %s", exc)

    return []


def parse_description(text: str) -> List[Span]:
    """Stub — plain text descriptions are not yet converted to spans."""
    return []
