"""
Tests for the mcp_server audit engine (parser + detectors + verify pass).

Each test writes a small synthetic codebase to tmp_path and runs the real
end-to-end engine on it, asserting on the report dict the MCP tools consume.
"""
import textwrap

from mcp_server.engine.engine import AuditEngine


def run(tmp_path, source: str) -> dict:
    (tmp_path / "agent.py").write_text(textwrap.dedent(source), encoding="utf-8")
    return AuditEngine().run_on_codebase(str(tmp_path)).to_dict()


def types_of(report: dict) -> set:
    return {f["type"] for f in report["findings"]}


# ── blocking_io ─────────────────────────────────────────────────────────────

def test_sync_http_flagged(tmp_path):
    report = run(tmp_path, """
        import requests
        async def handler():
            return requests.get("https://x.com")
    """)
    assert "blocking_io" in types_of(report)


def test_awaited_db_execute_not_flagged(tmp_path):
    report = run(tmp_path, """
        async def save(conn, q):
            await conn.execute(q)
    """)
    assert "blocking_io" not in types_of(report)


def test_time_sleep_in_async_flagged_high(tmp_path):
    report = run(tmp_path, """
        import time
        async def handler():
            time.sleep(1)
    """)
    f = next(f for f in report["findings"] if f["type"] == "blocking_io")
    assert f["severity"] == "high"
    assert f["verification"]["status"] == "confirmed"


def test_time_sleep_in_sync_not_flagged(tmp_path):
    report = run(tmp_path, """
        import time
        def batch():
            time.sleep(5)
    """)
    assert "blocking_io" not in types_of(report)


def test_subprocess_in_async_flagged(tmp_path):
    report = run(tmp_path, """
        import subprocess
        async def handler():
            subprocess.run(["ls"])
    """)
    assert "blocking_io" in types_of(report)


# ── sequential_tools ────────────────────────────────────────────────────────

def test_independent_awaits_flagged(tmp_path):
    report = run(tmp_path, """
        async def handler(q):
            a = await fetch_user(q)
            b = await fetch_orders(q)
            c = await fetch_tickets(q)
            return a, b, c
    """)
    f = next(f for f in report["findings"] if f["type"] == "sequential_tools")
    assert f["severity"] == "high"
    assert "asyncio.gather" in f["code_after"]


def test_data_dependent_awaits_not_flagged(tmp_path):
    report = run(tmp_path, """
        async def handler(q):
            user = await fetch_user(q)
            orders = await fetch_orders(user)
            return orders
    """)
    assert "sequential_tools" not in types_of(report)


def test_ordered_terminals_not_flagged(tmp_path):
    report = run(tmp_path, """
        async def handler(frame, other):
            a = await queue.put(frame)
            b = await sock.send(other)
            return a, b
    """)
    assert "sequential_tools" not in types_of(report)


# ── sync_output / streaming ─────────────────────────────────────────────────

def test_non_streaming_llm_call_flagged(tmp_path):
    report = run(tmp_path, """
        async def respond(client, msgs):
            resp = await client.chat.completions.create(model="gpt-4o", messages=msgs)
            return resp
    """)
    f = next(f for f in report["findings"] if f["type"] == "sync_output")
    assert f["severity"] == "high"
    assert f["verification"]["status"] == "confirmed"


def test_streaming_llm_call_not_flagged(tmp_path):
    report = run(tmp_path, """
        async def respond(client, msgs):
            resp = await client.chat.completions.create(model="gpt-4o", messages=msgs, stream=True)
            return resp
    """)
    assert "sync_output" not in types_of(report)


def test_forwarded_stream_resolved(tmp_path):
    report = run(tmp_path, """
        async def respond(client, msgs):
            params = {"model": "gpt-4o", "messages": msgs, "stream": True}
            resp = await client.chat.completions.create(**params)
            return resp
    """)
    assert "sync_output" not in types_of(report)


def test_embeddings_create_not_llm(tmp_path):
    report = run(tmp_path, """
        async def embed(client, text):
            resp = await client.embeddings.create(model="text-embedding-3-small", input=text)
            return resp
    """)
    assert "sync_output" not in types_of(report)


# ── cold_start (per-request client construction) ────────────────────────────

def test_client_in_request_fn_flagged(tmp_path):
    report = run(tmp_path, """
        import httpx
        async def handler(q):
            client = httpx.AsyncClient()
            return client
    """)
    assert "cold_start" in types_of(report)


def test_client_in_init_fn_not_flagged(tmp_path):
    report = run(tmp_path, """
        import httpx
        def build_client():
            return httpx.AsyncClient()
    """)
    assert "cold_start" not in types_of(report)


def test_client_at_module_level_not_flagged(tmp_path):
    report = run(tmp_path, """
        import httpx
        client = httpx.AsyncClient()
    """)
    assert "cold_start" not in types_of(report)


# ── cache_miss (repeated fully-static LLM calls) ────────────────────────────

def test_duplicate_static_llm_calls_flagged(tmp_path):
    report = run(tmp_path, """
        async def a(client):
            return await client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": "hi"}])
        async def b(client):
            return await client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": "hi"}])
    """)
    assert "cache_miss" in types_of(report)


def test_variable_arg_llm_calls_not_cache_flagged(tmp_path):
    report = run(tmp_path, """
        async def a(client, msgs):
            return await client.chat.completions.create(model="gpt-4o", messages=msgs)
        async def b(client, msgs):
            return await client.chat.completions.create(model="gpt-4o", messages=msgs)
    """)
    assert "cache_miss" not in types_of(report)


# ── report shape / verification ─────────────────────────────────────────────

def test_report_schema_and_verification(tmp_path):
    report = run(tmp_path, """
        import time
        async def handler():
            time.sleep(1)
    """)
    assert report["schema_version"] == "1.1"
    assert set(report["verification"]) == {"flagged", "confirmed", "dismissed", "confirmed_high_impact"}
    for f in report["findings"]:
        assert set(f["verification"]) == {"status", "reason", "impact"}
        assert f["verification"]["status"] in ("confirmed", "dismissed")


def test_empty_codebase(tmp_path):
    report = AuditEngine().run_on_codebase(str(tmp_path)).to_dict()
    assert report["files_scanned"] == 0
    assert report["findings"] == []
    assert report["verification"]["flagged"] == 0


def test_no_prefetch_location_survives_scoring(tmp_path):
    # 'A -> B' locations (no file) must not be mangled by file extraction.
    from mcp_server.engine.scorer import _file_of, _lines_of
    assert _file_of("fetch_a -> fetch_b") == "fetch_a -> fetch_b"
    assert _lines_of("fetch_a -> fetch_b") == []
