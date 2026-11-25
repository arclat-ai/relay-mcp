"""
Comprehensive tests for security, performance, AST parsing, and code-fixing improvements.
"""
import argparse
import json
import textwrap
from pathlib import Path

from mcp_server.engine.code_parser import CodeParser
from mcp_server.engine.detectors.sync_output import SyncOutputDetector
from mcp_server.engine.engine import AuditEngine
from mcp_server.engine.scorer import _file_of, _lines_of
from mcp_server.server import _atomic_write, _reindent_replacement, apply_fix, audit_codebase


def _run_src(tmp_path: Path, source: str) -> dict:
    (tmp_path / "agent.py").write_text(textwrap.dedent(source), encoding="utf-8")
    return AuditEngine().run_on_codebase(str(tmp_path)).to_dict()


# ── 1. Windows path extraction in scorer ───────────────────────────────────

def test_windows_drive_letter_paths():
    assert _file_of(r"D:\work\project\agent.py") == r"D:\work\project\agent.py"
    assert _file_of(r"D:\work\project\agent.py:42") == r"D:\work\project\agent.py"
    assert _file_of(r"D:\work\project\agent.py:10-25") == r"D:\work\project\agent.py"
    assert _file_of(r"requests.get@D:\work\agent.py:42") == r"D:\work\agent.py"
    assert _file_of("/home/user/agent.py:42") == "/home/user/agent.py"

    assert _lines_of(r"D:\work\project\agent.py") == []
    assert _lines_of(r"D:\work\project\agent.py:42") == [42]
    assert _lines_of(r"D:\work\project\agent.py:10-25") == [10, 25]


# ── 2. Type-annotated variable assignments (AnnAssign) ──────────────────────

def test_annassign_sequential_tools(tmp_path):
    report = _run_src(tmp_path, """
        async def handler(q):
            user: User = await fetch_user(q)
            orders: list = await fetch_orders(q)
            return user, orders
    """)
    findings = [f for f in report["findings"] if f["type"] == "sequential_tools"]
    assert len(findings) == 1
    f = findings[0]
    assert "user, orders = await asyncio.gather(" in f["code_after"]


# ── 3. Tuple unpacking target syntax ───────────────────────────────────────

def test_tuple_unpacking_sequential_tools(tmp_path):
    report = _run_src(tmp_path, """
        async def handler(q):
            a, b = await fetch_coords(q)
            c = await fetch_profile(q)
            return a, b, c
    """)
    findings = [f for f in report["findings"] if f["type"] == "sequential_tools"]
    assert len(findings) == 1
    f = findings[0]
    assert "(a, b), c = await asyncio.gather(" in f["code_after"]


# ── 4. Indentation-aware replacement ───────────────────────────────────────

def test_reindent_replacement_indented_function():
    src = (
        "async def handler(q):\n"
        "    a = await fetch_user(q)\n"
        "    b = await fetch_orders(q)\n"
        "    return a, b\n"
    )
    before = "a = await fetch_user(q)\nb = await fetch_orders(q)"
    after = "a, b = await asyncio.gather(\n    fetch_user(q),\n    fetch_orders(q)\n)"

    new_src, actual_before, indented_after = _reindent_replacement(src, before, after)
    assert new_src is not None
    assert actual_before == "    a = await fetch_user(q)\n    b = await fetch_orders(q)"
    assert indented_after == "    a, b = await asyncio.gather(\n        fetch_user(q),\n        fetch_orders(q)\n    )"
    assert "    a, b = await asyncio.gather(" in new_src
    assert new_src.endswith("\n")


# ── 5. apply_fix security path traversal check ─────────────────────────────

def test_apply_fix_security_path_traversal(tmp_path):
    agent_file = tmp_path / "agent.py"
    agent_file.write_text(textwrap.dedent("""
        async def handler(q):
            a = await fetch_user(q)
            b = await fetch_orders(q)
            return a, b
    """), encoding="utf-8")

    audit_codebase(str(tmp_path), write_report=False)

    outside = tmp_path.parent / "outside_project.py"
    outside.write_text("evil = 1\n", encoding="utf-8")

    res = apply_fix(1, file_path=str(outside), dry_run=False)
    assert "Security error" in res
    assert outside.read_text(encoding="utf-8") == "evil = 1\n"


# ── 6. apply_fix real-world indentation patching ───────────────────────────

def test_apply_fix_on_indented_function(tmp_path):
    agent_file = tmp_path / "agent.py"
    agent_file.write_text(textwrap.dedent("""
        async def handler(q):
            a = await fetch_user(q)
            b = await fetch_orders(q)
            return a, b
    """), encoding="utf-8")

    audit_codebase(str(tmp_path), write_report=False)
    res = apply_fix(1, file_path=str(agent_file), dry_run=False)
    assert "✅ Fix applied" in res
    content = agent_file.read_text(encoding="utf-8")
    assert "a, b = await asyncio.gather(" in content
    assert "    fetch_user(q)," in content


# ── 7. Atomic file write ───────────────────────────────────────────────────

def test_atomic_write(tmp_path):
    target = tmp_path / "sub" / "output.txt"
    _atomic_write(target, "hello atomic world", mode=0o600)
    assert target.read_text(encoding="utf-8") == "hello atomic world"

    _atomic_write(target, "updated content")
    assert target.read_text(encoding="utf-8") == "updated content"


# ── 8. Cache miss detector has empty code_after ────────────────────────────

def test_cache_miss_no_code_after(tmp_path):
    report = _run_src(tmp_path, """
        async def a(client):
            return await client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": "hi"}])
        async def b(client):
            return await client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": "hi"}])
    """)
    cm = next(f for f in report["findings"] if f["type"] == "cache_miss")
    assert cm["code_after"] == ""
    assert cm["code_before"] == ""


# ── 9. Directory pruning with os.walk ───────────────────────────────────────

def test_directory_pruning(tmp_path):
    venv_dir = tmp_path / ".venv" / "lib"
    venv_dir.mkdir(parents=True)
    (venv_dir / "ignored.py").write_text("x = 1\n", encoding="utf-8")

    node_dir = tmp_path / "node_modules" / "pkg"
    node_dir.mkdir(parents=True)
    (node_dir / "ignored.py").write_text("x = 1\n", encoding="utf-8")

    (tmp_path / "valid.py").write_text("async def f(): pass\n", encoding="utf-8")

    parser = CodeParser()
    parser.parse_directory(str(tmp_path))
    assert parser.files_scanned == 1


# ── 10. Single-pass definition indexing (def_index) ─────────────────────────

def test_single_pass_def_index(tmp_path):
    (tmp_path / "lib.py").write_text(textwrap.dedent("""
        def cheap_calc(x):
            return x + 1

        async def io_fetch(q):
            await do_something()
    """), encoding="utf-8")

    parser = CodeParser()
    parser.parse_directory(str(tmp_path))
    assert parser.def_index.get("cheap_calc") == "cheap"
    assert parser.def_index.get("io_fetch") == "io"


# ── 11. Custom detector registry in AuditEngine ────────────────────────────

def test_custom_detector_registry(tmp_path):
    (tmp_path / "agent.py").write_text(textwrap.dedent("""
        import requests
        async def handler():
            requests.get("https://x.com")
            return await client.chat.completions.create(model="gpt-4o", messages=[])
    """), encoding="utf-8")

    # Only run SyncOutputDetector
    engine = AuditEngine(detectors=[SyncOutputDetector()])
    report = engine.run_on_codebase(str(tmp_path)).to_dict()
    types = {f["type"] for f in report["findings"]}
    assert "sync_output" in types
    assert "blocking_io" not in types


# ── 12. CLI report command atomic write ────────────────────────────────────

def test_cli_report_cmd(tmp_path):
    from mcp_server.cli import cmd_report
    (tmp_path / "agent.py").write_text("async def f(): pass\n", encoding="utf-8")

    out_file = tmp_path / "my-report.json"
    args = argparse.Namespace(directory=str(tmp_path), output=str(out_file))
    code = cmd_report(args)
    assert code == 0
    assert out_file.is_file()
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data["generator"] == "relay-cli"


# ── 13. get_findings and verify_audit tools ────────────────────────────────

def test_mcp_get_findings_and_verify_audit(tmp_path):
    from mcp_server.server import get_findings, verify_audit
    (tmp_path / "agent.py").write_text(textwrap.dedent("""
        import time
        async def handler():
            time.sleep(1)
    """), encoding="utf-8")

    audit_codebase(str(tmp_path), write_report=False)

    all_res = get_findings()
    assert "time.sleep" in all_res

    high_res = get_findings(severity="high")
    assert "time.sleep" in high_res

    none_res = get_findings(finding_type="nonexistent_type")
    assert "No findings match the given filters" in none_res

    v_res = verify_audit()
    assert "## Relay Verification" in v_res
    assert "confirmed" in v_res


# ── 14. apply_fix edge cases ───────────────────────────────────────────────

def test_apply_fix_invalid_rank_and_extension(tmp_path):
    (tmp_path / "agent.py").write_text("async def f(): pass\n", encoding="utf-8")
    audit_codebase(str(tmp_path), write_report=False)

    res1 = apply_fix(999, dry_run=True)
    assert "No finding with rank 999" in res1

    res2 = apply_fix(1, file_path="not_a_python_file.txt", dry_run=True)
    assert "This finding has no single file location - pass file_path explicitly." in res2 or "No finding with rank" in res2


# ── 15. Syntax error in target file handled gracefully ─────────────────────

def test_syntax_error_resilience(tmp_path):
    (tmp_path / "broken.py").write_text("def broken syntax (: \n", encoding="utf-8")
    (tmp_path / "valid.py").write_text("def ok(): pass\n", encoding="utf-8")

    parser = CodeParser()
    parser.parse_directory(str(tmp_path))
    # broken.py is skipped cleanly without raising SyntaxError
    assert parser.files_scanned == 2


# ── 16. CLI scan and verify CI gate ────────────────────────────────────────

def test_cli_scan_and_verify(tmp_path):
    from mcp_server.cli import cmd_scan, cmd_verify
    (tmp_path / "agent.py").write_text(textwrap.dedent("""
        import time
        async def handler():
            time.sleep(1)
    """), encoding="utf-8")

    args_scan = argparse.Namespace(directory=str(tmp_path), json=True)
    code_scan = cmd_scan(args_scan)
    assert code_scan == 0

    args_verify_pass = argparse.Namespace(directory=str(tmp_path), json=False, fail_on="none")
    assert cmd_verify(args_verify_pass) == 0

    args_verify_fail = argparse.Namespace(directory=str(tmp_path), json=False, fail_on="high")
    assert cmd_verify(args_verify_fail) == 1


# ── 17. Cloud SDK synchronous calls in async functions ─────────────────────

def test_cloud_sdk_blocking_io(tmp_path):
    report = _run_src(tmp_path, """
        async def handler(s3, blob):
            data = s3.get_object(Bucket="my-bucket", Key="file.txt")
            content = blob.download_as_bytes()
            return data, content
    """)
    cloud_findings = [
        f for f in report["findings"]
        if f["type"] == "blocking_io" and f["title"] == "Make cloud SDK calls async"
    ]
    assert len(cloud_findings) == 1
    assert cloud_findings[0]["occurrences"] == 2
    assert cloud_findings[0]["severity"] == "high"
    assert "asyncio.to_thread" in cloud_findings[0]["code_after"]


def test_cloud_client_in_request_fn(tmp_path):
    report = _run_src(tmp_path, """
        import boto3
        async def handler(q):
            s3 = boto3.client("s3")
            return s3
    """)
    cold_starts = [f for f in report["findings"] if f["type"] == "cold_start"]
    assert len(cold_starts) == 1
    assert "boto3.client" in cold_starts[0]["description"]


# ── 18. Rich unified diff format in apply_fix ──────────────────────────────

def test_apply_fix_rich_unified_diff(tmp_path):
    agent_file = tmp_path / "agent.py"
    agent_file.write_text(textwrap.dedent("""
        async def handler(q):
            a = await fetch_user(q)
            b = await fetch_orders(q)
            return a, b
    """), encoding="utf-8")

    audit_codebase(str(tmp_path), write_report=False)

    # Dry run diff output
    dry_res = apply_fix(1, file_path=str(agent_file), dry_run=True)
    assert "```diff" in dry_res
    assert "--- a/" in dry_res
    assert "+++ b/" in dry_res
    assert "-    a = await fetch_user(q)" in dry_res
    assert "+    a, b = await asyncio.gather(" in dry_res

    # Applied diff output
    applied_res = apply_fix(1, file_path=str(agent_file), dry_run=False)
    assert "✅ Fix applied" in applied_res
    assert "```diff" in applied_res
    assert "--- a/" in applied_res
    assert "+++ b/" in applied_res


