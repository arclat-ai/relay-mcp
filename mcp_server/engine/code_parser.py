"""
Parses Python agent codebases using AST analysis.

Produces Span objects that carry REAL source snippets and precise file:line
locations. Analysis is scoped per-function so detectors never group calls
across unrelated functions or files.
"""
import ast
import uuid
from pathlib import Path
from typing import List, Optional

from mcp_server.engine.base_detector import Span

_SKIP_DIRS = {"venv", ".venv", "__pycache__", ".git", "node_modules", ".mypy_cache",
              "tests", "test", "examples", "docs"}

# Precise LLM-call detection. We match on the FINAL attribute of the call chain
# plus a context token, so `loop.run_in_executor(...)` is never mistaken for an
# LLM call.
_LLM_TERMINALS = {"create", "acreate", "generate", "agenerate",
                  "complete", "acomplete", "stream", "astream"}
_LLM_CONTEXT = ("messages", "completions", "responses", "chat", "llm", "model",
                "client", "anthropic", "openai", "gemini", "claude", "completion")
# Non-generative endpoints that also end in `.create` but where token streaming
# is meaningless (STT/TTS/embeddings/moderation/image).
_LLM_EXCLUDE = ("transcription", "translation", "embedding", "moderation",
                "speech", "image", "audio", "voice", "vector")
_STREAM_TERMINALS = {"stream", "astream"}

_SYNC_HTTP = {"requests.get", "requests.post", "requests.put", "requests.delete",
              "requests.patch", "requests.head"}
_SYNC_DB = {"session.execute", "cursor.execute", "collection.find", "conn.execute"}

# Awaited calls whose ordering matters (side effects / pipeline emits). These are
# NEVER treated as independent parallelizable work, even if assigned.
_ORDERED_TERMINALS = {
    "send", "send_nowait", "write", "emit", "publish", "flush", "close",
    "commit", "ack", "push", "push_frame", "push_error", "sleep", "cancel",
    "wait", "drain", "join", "put", "release", "acquire", "seek", "connect",
    "disconnect", "start", "stop", "run", "run_in_executor", "gather",
}


def _node_name(node: ast.expr) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{_node_name(node.value)}.{node.attr}"
    if isinstance(node, ast.Call):
        return _node_name(node.func)
    return ""


def _terminal(call_name: str) -> str:
    return call_name.rsplit(".", 1)[-1] if call_name else ""


def _is_llm_call(call_name: str) -> bool:
    term = _terminal(call_name)
    if term not in _LLM_TERMINALS:
        return False
    lowered = call_name.lower()
    if any(bad in lowered for bad in _LLM_EXCLUDE):
        return False
    return any(ctx in lowered for ctx in _LLM_CONTEXT)


def _is_streaming(call: ast.Call, call_name: str) -> bool:
    if _terminal(call_name) in _STREAM_TERMINALS:
        return True
    for kw in call.keywords:
        if kw.arg == "stream" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
            return True
    return False


def _forwarded_names(call: ast.Call) -> set:
    """Names forwarded as **kwargs into the call, e.g. `.create(**params)` -> {'params'}."""
    return {kw.value.id for kw in call.keywords
            if kw.arg is None and isinstance(kw.value, ast.Name)}


def _resolve_forwarded_stream(func: ast.AST, names: set):
    """Best-effort: within `func`, decide whether the forwarded kwargs dict(s) set
    `stream`. Returns True (streaming), False (explicitly non-streaming), or None
    (can't tell — leave it as unknown). Last write wins for repeated assignments.

    Recognizes the two common patterns:
        params = {..., "stream": True}          # dict literal
        params["stream"] = True                 # subscript assignment
    """
    if not names:
        return None
    resolved = None
    for stmt in ast.walk(func):
        if not isinstance(stmt, ast.Assign):
            continue
        for tgt in stmt.targets:
            # params["stream"] = <const>
            if (isinstance(tgt, ast.Subscript) and isinstance(tgt.value, ast.Name)
                    and tgt.value.id in names
                    and isinstance(tgt.slice, ast.Constant) and tgt.slice.value == "stream"
                    and isinstance(stmt.value, ast.Constant)):
                resolved = bool(stmt.value.value)
            # params = {..., "stream": <const>, ...}
            if (isinstance(tgt, ast.Name) and tgt.id in names
                    and isinstance(stmt.value, ast.Dict)):
                for k, v in zip(stmt.value.keys, stmt.value.values):
                    if (isinstance(k, ast.Constant) and k.value == "stream"
                            and isinstance(v, ast.Constant)):
                        resolved = bool(v.value)
    return resolved


def _names_used(node: ast.AST) -> set:
    """All identifier names referenced (loaded) anywhere under node."""
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}


def _assign_targets(node: ast.Assign) -> set:
    out = set()
    for tgt in node.targets:
        out |= {n.id for n in ast.walk(tgt) if isinstance(n, ast.Name)}
    return out


def _make_span(name, span_type, cursor_ms, duration_ms, metadata):
    span = Span(
        id=str(uuid.uuid4())[:8],
        name=name,
        start_ms=cursor_ms,
        end_ms=cursor_ms + duration_ms,
        duration_ms=duration_ms,
        span_type=span_type,
        metadata=metadata,
    )
    return span, cursor_ms + duration_ms


class CodeParser:
    def parse_directory(self, directory: str) -> List[Span]:
        spans: List[Span] = []
        cursor_ms = 0
        self.files_scanned = 0
        for py_file in sorted(Path(directory).rglob("*.py")):
            if any(part in _SKIP_DIRS for part in py_file.parts):
                continue
            self.files_scanned += 1
            new_spans, cursor_ms = self._parse_file(str(py_file), cursor_ms)
            spans.extend(new_spans)
        return spans

    def _parse_file(self, file_path: str, cursor_ms: int):
        try:
            source = Path(file_path).read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(source)
        except (SyntaxError, ValueError):
            return [], cursor_ms

        self._source = source
        self._file = file_path
        # Calls that are directly awaited are NOT synchronous/blocking, even if
        # the method name matches a known sync DB/HTTP API (e.g. asyncpg's
        # `await conn.execute(...)`).
        self._awaited_calls = {
            id(n.value) for n in ast.walk(tree)
            if isinstance(n, ast.Await) and isinstance(n.value, ast.Call)
        }
        spans: List[Span] = []

        for node in ast.walk(tree):
            # Synchronous blocking I/O — flagged anywhere.
            if isinstance(node, ast.Call):
                spans_here, cursor_ms = self._blocking_io(node, cursor_ms)
                spans.extend(spans_here)

            # LLM calls + sequential independent work — scoped per function.
            if isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
                spans_here, cursor_ms = self._scan_function(node, cursor_ms)
                spans.extend(spans_here)

        return spans, cursor_ms

    def _snippet(self, node: ast.AST) -> str:
        seg = ast.get_source_segment(self._source, node)
        return seg.strip() if seg else ""

    def _blocking_io(self, node: ast.Call, cursor_ms: int):
        # Awaited calls run on the event loop asynchronously — not blocking.
        if id(node) in self._awaited_calls:
            return [], cursor_ms
        call_name = _node_name(node.func)
        line = getattr(node, "lineno", 0)
        if call_name in _SYNC_HTTP:
            span, cursor_ms = _make_span(
                name=f"{call_name}@{self._file}:{line}",
                span_type="api_call", cursor_ms=cursor_ms, duration_ms=500,
                metadata={"async": False, "code": self._snippet(node),
                          "file": self._file, "line": line},
            )
            return [span], cursor_ms
        if call_name in _SYNC_DB:
            span, cursor_ms = _make_span(
                name=f"{call_name}@{self._file}:{line}",
                span_type="db_query", cursor_ms=cursor_ms, duration_ms=200,
                metadata={"async": False, "code": self._snippet(node),
                          "file": self._file, "line": line},
            )
            return [span], cursor_ms
        return [], cursor_ms

    def _scan_function(self, func: ast.AST, cursor_ms: int):
        """Emit LLM-call spans and groups of genuinely-independent awaited calls."""
        spans: List[Span] = []

        # 1. LLM calls in this function.
        for n in ast.walk(func):
            if isinstance(n, ast.Await) and isinstance(n.value, ast.Call):
                call_name = _node_name(n.value.func)
                if _is_llm_call(call_name):
                    streaming = _is_streaming(n.value, call_name)
                    # If args are forwarded via **kwargs we can't see stream=...
                    # directly — but try to resolve it from the same function first.
                    unknown = any(kw.arg is None for kw in n.value.keywords)
                    if not streaming and unknown:
                        resolved = _resolve_forwarded_stream(func, _forwarded_names(n.value))
                        if resolved is not None:
                            streaming = resolved      # confirmed one way or the other
                            unknown = False           # no longer a guess
                    line = getattr(n, "lineno", 0)
                    span, cursor_ms = _make_span(
                        name=f"{self._file}:{line}",
                        span_type="llm_call", cursor_ms=cursor_ms,
                        duration_ms=500 if streaming else 3000,
                        metadata={"streaming": streaming, "streaming_unknown": unknown,
                                  "code": self._snippet(n), "file": self._file,
                                  "line": line, "call": call_name},
                    )
                    spans.append(span)

        # 2. Sequential independent awaited assignments, block-scoped.
        for block in self._statement_blocks(func):
            groups = self._independent_runs(block)
            for group in groups:
                gid = str(uuid.uuid4())[:8]
                for stmt in group:
                    call = stmt.value.value  # Assign -> Await -> Call
                    line = getattr(stmt, "lineno", 0)
                    span, cursor_ms = _make_span(
                        name=_node_name(call.func) or f"tool@{line}",
                        span_type="tool_call", cursor_ms=cursor_ms, duration_ms=400,
                        metadata={"group_id": gid, "code": self._snippet(stmt),
                                  "call_src": self._snippet(call),
                                  "targets": sorted(_assign_targets(stmt)),
                                  "file": self._file, "line": line},
                    )
                    spans.append(span)

        return spans, cursor_ms

    def _statement_blocks(self, func: ast.AST):
        """Yield each contiguous statement list (function body + nested blocks)."""
        for n in ast.walk(func):
            for attr in ("body", "orelse", "finalbody"):
                block = getattr(n, attr, None)
                if isinstance(block, list) and block and all(isinstance(s, ast.stmt) for s in block):
                    yield block

    def _independent_runs(self, block: list):
        """Find maximal runs (>=2) of consecutive `x = await call()` statements
        that are provably data-independent and side-effect-free."""
        def is_candidate(stmt) -> Optional[ast.Assign]:
            if (isinstance(stmt, ast.Assign)
                    and isinstance(stmt.value, ast.Await)
                    and isinstance(stmt.value.value, ast.Call)):
                call_name = _node_name(stmt.value.value.func)
                if _terminal(call_name) in _ORDERED_TERMINALS:
                    return None
                return stmt
            return None

        runs, current, produced = [], [], set()
        for stmt in block:
            cand = is_candidate(stmt)
            if cand is None:
                if len(current) >= 2:
                    runs.append(current)
                current, produced = [], set()
                continue
            # Independent iff its call references none of the names produced
            # by earlier members of the current run.
            used = _names_used(cand.value.value)
            if produced & used:
                if len(current) >= 2:
                    runs.append(current)
                current, produced = [], set()
            current.append(cand)
            produced |= _assign_targets(cand)
        if len(current) >= 2:
            runs.append(current)
        return runs
