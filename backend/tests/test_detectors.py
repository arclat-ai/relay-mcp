import pytest
from app.engine.ingester import parse_logs
from app.engine.detectors.sync_output import SyncOutputDetector
from app.engine.detectors.sequential_tools import SequentialToolDetector
from app.engine.detectors.cache_miss import CacheMissDetector
from app.engine.detectors.blocking_io import BlockingIODetector
from app.engine.detectors.cold_start import ColdStartDetector
from app.engine.detectors.prefetch import PrefetchDetector

SAMPLE_LOGS = """
{
  "pipeline_name": "Customer Support Agent",
  "framework": "langchain",
  "spans": [
    {"id": "span_001", "name": "agent_loop_init", "start_ms": 0, "end_ms": 620, "span_type": "agent_loop", "metadata": {}},
    {"id": "span_002", "name": "llm_call_classify", "start_ms": 620, "end_ms": 3800, "span_type": "llm_call", "metadata": {"prompt_hash": "abc123", "streaming": false}},
    {"id": "span_003", "name": "tool_call_fetch_user", "start_ms": 3800, "end_ms": 4950, "span_type": "tool_call", "metadata": {}},
    {"id": "span_004", "name": "tool_call_fetch_orders", "start_ms": 4952, "end_ms": 6100, "span_type": "tool_call", "metadata": {}},
    {"id": "span_005", "name": "tool_call_fetch_tickets", "start_ms": 6102, "end_ms": 7300, "span_type": "tool_call", "metadata": {}},
    {"id": "span_006", "name": "db_query_log", "start_ms": 7300, "end_ms": 7650, "span_type": "db_query", "metadata": {"async": false}},
    {"id": "span_007", "name": "llm_call_classify", "start_ms": 7650, "end_ms": 10900, "span_type": "llm_call", "metadata": {"prompt_hash": "abc123", "streaming": false}},
    {"id": "span_008", "name": "llm_call_respond", "start_ms": 10900, "end_ms": 14200, "span_type": "llm_call", "metadata": {"prompt_hash": "def456", "streaming": false}}
  ]
}
"""

@pytest.fixture
def sample_timeline():
    return parse_logs(SAMPLE_LOGS)

def test_sync_output_detector(sample_timeline):
    detector = SyncOutputDetector()
    findings = detector.detect(sample_timeline)
    
    assert len(findings) == 3
    names = [f.location for f in findings]
    assert "llm_call_classify" in names
    assert "llm_call_respond" in names

def test_sequential_tools_detector(sample_timeline):
    detector = SequentialToolDetector()
    findings = detector.detect(sample_timeline)
    
    assert len(findings) == 1
    assert findings[0].severity == "high" # 3 tools
    assert "tool_call_fetch_user" in findings[0].location

def test_cache_miss_detector(sample_timeline):
    detector = CacheMissDetector()
    findings = detector.detect(sample_timeline)
    
    assert len(findings) == 1
    assert findings[0].location == "llm_call_classify"

def test_blocking_io_detector(sample_timeline):
    detector = BlockingIODetector()
    findings = detector.detect(sample_timeline)
    
    assert len(findings) == 1
    assert findings[0].location == "db_query_log"

def test_cold_start_detector(sample_timeline):
    detector = ColdStartDetector()
    findings = detector.detect(sample_timeline)
    
    assert len(findings) == 1
    assert findings[0].location == "agent_loop_init"
    assert findings[0].time_lost_ms == 620 - 50
