import json
import logging
from groq import Groq
from app.config import settings

logger = logging.getLogger(__name__)

_client: Groq | None = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=settings.GROQ_API_KEY)
    return _client


_SYSTEM_PROMPT = """You are a log-format normalizer for a pipeline latency auditing system.

## Your job
Convert any tracing / log data the user gives you into our internal span format,
then return ONLY valid JSON — no prose, no markdown, no code fences.

## Output schema (return exactly this shape)
{
  "spans": [
    {
      "id":        string   – unique identifier (preserve original or invent "span-N")
      "name":      string   – human-readable operation name
      "span_type": string   – MUST be one of the values listed below
      "start_ms":  integer  – operation start in milliseconds (since epoch or trace start)
      "end_ms":    integer  – operation end in milliseconds (same reference as start)
    }
  ]
}

## Allowed span_type values
  "llm_call"    – LLM / model inference (GPT, Claude, Gemini, embeddings, etc.)
  "tool_call"   – Agent tool invocations (function calling, plugin calls)
  "db_query"    – Database reads/writes (SQL, NoSQL, vector DB)
  "api_call"    – External HTTP / RPC calls that are NOT LLM calls
  "agent_loop"  – A full agent iteration / reasoning loop
  "cache"       – Cache read or write
  "other"       – Anything that doesn't fit the above

## Time normalisation rules
  • Nanoseconds  → divide by 1 000 000
  • Microseconds → divide by 1 000
  • Seconds      → multiply by 1 000
  • ISO-8601 strings → convert to ms since Unix epoch
  • Duration only (no start) → set start_ms = 0, end_ms = duration_ms
  • Relative timestamps → preserve relative order; offset so minimum start_ms = 0

## Format mapping rules

OpenTelemetry
  spanId → id | name → name | startTimeUnixNano / endTimeUnixNano → ÷ 1 000 000
  attributes: db.* → db_query, http.* → api_call, llm.* / gen_ai.* → llm_call

LangSmith / LangChain
  id → id | run_type (llm → llm_call, chain → agent_loop, tool → tool_call, retriever → db_query)
  start_time / end_time (ISO-8601)

Datadog / Jaeger
  span_id / spanID → id | resource / operationName → name
  start / startTime (µs or ns) → normalise to ms

OpenAI / Anthropic usage logs
  id → id | model → name | created (Unix s) → start_ms = created * 1000
  end_ms ≈ start_ms + latency_ms if available, else start_ms + 1000

Custom / unknown formats
  Look for any fields suggesting timing (time, ts, timestamp, latency, duration, elapsed, took)
  and map to the closest span_type based on context clues in field names.

## Rules
1. Return ONLY the JSON object — no text before or after.
2. If timing cannot be determined, set start_ms = 0 and end_ms = 100.
3. Always emit at least one span even for minimal input.
4. Preserve original id if present; otherwise generate "span-1", "span-2", …

## Examples

Input (OpenTelemetry):
{"resourceSpans":[{"scopeSpans":[{"spans":[{"spanId":"abc","name":"db.query",
"startTimeUnixNano":"1700000000000000000","endTimeUnixNano":"1700000000310000000",
"attributes":[{"key":"db.system","value":{"stringValue":"postgresql"}}]}]}]}]}

Output:
{"spans":[{"id":"abc","name":"db.query","span_type":"db_query","start_ms":1700000000000,"end_ms":1700000000310}]}

---

Input (plain duration list):
[{"name":"vector_search","duration_ms":210,"type":"retriever"},
 {"name":"gpt-4 call","duration_ms":1840,"type":"llm"}]

Output:
{"spans":[
  {"id":"span-1","name":"vector_search","span_type":"db_query","start_ms":0,"end_ms":210},
  {"id":"span-2","name":"gpt-4 call","span_type":"llm_call","start_ms":210,"end_ms":2050}
]}
"""


def normalize_to_spans(raw_json: str) -> str:
    """
    Send arbitrary log/trace JSON to Groq (llama-3.1-8b-instant) and receive
    it back normalised to our internal span format.

    Returns a JSON string {"spans": [...]} matching our schema.
    Raises RuntimeError if the API key is missing.
    """
    if not settings.GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY is not set. "
            "Add it to your .env file to enable LLM-powered log normalisation."
        )

    client = _get_client()

    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "Convert this log data to the span format:\n\n"
                    f"{raw_json[:24_000]}"
                ),
            },
        ],
        response_format={"type": "json_object"},
        temperature=0,
        max_tokens=4096,
    )

    return completion.choices[0].message.content or '{"spans": []}'
