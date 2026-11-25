"""
Parses Python agent codebases using AST analysis.

Produces Span objects that carry REAL source snippets and precise file:line
locations. Analysis is scoped per-function so detectors never group calls
across unrelated functions or files.
"""
import ast
import hashlib
import itertools
import os
from pathlib import Path

from mcp_server.engine.base_detector import Span

_SKIP_DIRS = {
    "venv", ".venv", "env", ".env", "__pycache__", ".git", "node_modules",
    ".mypy_cache", ".pytest_cache", ".ruff_cache", "tests", "test",
    "examples", "docs", "site-packages", "dist", "build", ".tox", ".nox"
}

_SPAN_ID_COUNTER = itertools.count(1)
_GROUP_ID_COUNTER = itertools.count(1)

_IO_MODULES = {"requests", "httpx", "aiohttp", "urllib", "socket", "subprocess",
               "sqlite3", "psycopg", "psycopg2", "asyncpg", "aiofiles", "boto3",
               "redis", "pymongo", "smtplib", "ftplib"}
_IO_METHODS = {"post", "put", "delete", "patch", "request", "execute", "read",
               "write", "recv", "sendall", "fetch", "query", "download",
               "upload", "aread", "aiter_lines"}
_IO_BUILTINS = {"open"}


def _is_stub_body(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    body = node.body
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
        body = body[1:]
    if not body:
        return True
    for s in body:
        if isinstance(s, ast.Pass):
            continue
        if isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant) and s.value.value is ...:
            continue
        if isinstance(s, ast.Raise):
            continue
        return False
    return True


def _classify_function_def(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    """Cost class of a single function definition: 'io', 'cheap', or 'unknown'."""
    if _is_stub_body(node):
        return "unknown"
    for n in ast.walk(node):
        if isinstance(n, ast.Await):
            return "io"
        if isinstance(n, ast.Name) and n.id in _IO_MODULES:
            return "io"
        if isinstance(n, ast.Call):
            fn = n.func
            if isinstance(fn, ast.Name) and fn.id in _IO_BUILTINS:
                return "io"
            if isinstance(fn, ast.Attribute) and fn.attr in _IO_METHODS:
                return "io"
    return "cheap"

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
              "requests.patch", "requests.head", "requests.request",
              "urllib.request.urlopen", "urlopen"}
_SYNC_DB = {"session.execute", "cursor.execute", "collection.find", "conn.execute"}
_SYNC_CLOUD_CALLS = {
    "boto3.client", "boto3.resource",
    "s3.get_object", "s3.put_object", "s3.delete_object", "s3.list_objects", "s3.list_objects_v2",
    "s3.download_file", "s3.upload_file", "s3.download_fileobj", "s3.upload_fileobj",
    "s3_client.get_object", "s3_client.put_object", "s3_client.delete_object",
    "dynamodb.get_item", "dynamodb.put_item", "dynamodb.update_item", "dynamodb.delete_item", "dynamodb.query", "dynamodb.scan",
    "sqs.send_message", "sqs.receive_messages", "sqs.delete_message", "sns.publish",
    "blob.download_as_bytes", "blob.download_as_string", "blob.download_as_text",
    "blob.upload_from_string", "blob.upload_from_filename", "blob.upload_from_file",
}
_SYNC_CLOUD_TERMINALS = {
    "get_object", "put_object", "download_file", "upload_file",
    "download_as_bytes", "download_as_string", "download_as_text",
    "upload_from_string", "upload_from_filename",
}
# Blocking calls only meaningful inside an async function (in a sync script
# `time.sleep` is fine; on the event loop it stalls every concurrent task).
_SYNC_SLEEP = {"time.sleep"}
_SYNC_SUBPROC = {"subprocess.run", "subprocess.call", "subprocess.check_output",
                 "subprocess.check_call", "os.system"}

# Per-request client construction: building one of these inside an ordinary
# function (rather than at startup) pays TLS/connection setup on every call.
_CLIENT_CTORS = {"OpenAI", "AsyncOpenAI", "Anthropic", "AsyncAnthropic",
                 "openai.OpenAI", "openai.AsyncOpenAI",
                 "anthropic.Anthropic", "anthropic.AsyncAnthropic",
                 "httpx.Client", "httpx.AsyncClient",
                 "aiohttp.ClientSession", "requests.Session",
                 "boto3.client", "boto3.resource",
                 "storage.Client", "bigquery.Client", "firestore.Client"}
# Function names where constructing a client is expected (startup / DI paths).
_INIT_NAME_TOKENS = ("init", "setup", "client", "connect", "start", "boot",
                     "main", "create", "build", "factory", "session", "lifespan")

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
    (can't tell - leave it as unknown). Last write wins for repeated assignments.

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
                for k, v in zip(stmt.value.keys, stmt.value.values, strict=True):
                    if (isinstance(k, ast.Constant) and k.value == "stream"
                            and isinstance(v, ast.Constant)):
                        resolved = bool(v.value)
    return resolved


def _static_prompt_hash(call: ast.Call) -> str | None:
    """Hash of a *fully static* LLM call - every arg/kwarg value is a constant
    (or a structure of constants). Two call sites with the same hash send the
    same input every time, so the response is cacheable. Calls with variable
    args get no hash: their runtime inputs differ."""
    def _const(node: ast.AST) -> bool:
        if isinstance(node, ast.Constant):
            return True
        if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
            return all(_const(e) for e in node.elts)
        if isinstance(node, ast.Dict):
            return all(k is not None and _const(k) and _const(v)
                       for k, v in zip(node.keys, node.values, strict=True))
        return False

    if not call.args and not call.keywords:
        return None
    if any(not _const(a) for a in call.args):
        return None
    if any(kw.arg is None or not _const(kw.value) for kw in call.keywords):
        return None
    src = ast.dump(ast.Call(func=ast.Name(id="_"), args=call.args, keywords=call.keywords))
    return hashlib.md5(src.encode()).hexdigest()[:12]


def _names_used(node: ast.AST) -> set:
    """All identifier names referenced (loaded) anywhere under node."""
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}


def _assign_targets(node: ast.stmt) -> set:
    out = set()
    if isinstance(node, ast.Assign):
        for tgt in node.targets:
            out |= {n.id for n in ast.walk(tgt) if isinstance(n, ast.Name)}
    elif isinstance(node, ast.AnnAssign):
        out |= {n.id for n in ast.walk(node.target) if isinstance(n, ast.Name)}
    return out


def _target_str(stmt: ast.stmt) -> str:
    if isinstance(stmt, ast.AnnAssign):
        if isinstance(stmt.target, ast.Name):
            return stmt.target.id
        return "_"
    if isinstance(stmt, ast.Assign) and stmt.targets:
        tgt = stmt.targets[0]
        if isinstance(tgt, ast.Name):
            return tgt.id
        if isinstance(tgt, (ast.Tuple, ast.List)):
            names = [n.id for n in tgt.elts if isinstance(n, ast.Name)]
            return f"({', '.join(names)})" if names else "_"
    return "_"


def _make_span(name, span_type, cursor_ms, duration_ms, metadata):
    span = Span(
        id=f"s{next(_SPAN_ID_COUNTER)}",
        name=name,
        start_ms=cursor_ms,
        end_ms=cursor_ms + duration_ms,
        duration_ms=duration_ms,
        span_type=span_type,
        metadata=metadata,
    )
    return span, cursor_ms + duration_ms


class CodeParser:
    def __init__(self):
        self.files_scanned = 0
        self.def_index: dict[str, str] = {}

    def _absorb_def(self, name: str, cls: str) -> None:
        cur = self.def_index.get(name)
        if cur == "io" or cls == "io":
            self.def_index[name] = "io"
        elif cur == "cheap" or cls == "cheap":
            self.def_index[name] = "cheap"
        else:
            self.def_index[name] = "unknown"

    def parse_directory(self, directory: str) -> list[Span]:
        spans: list[Span] = []
        cursor_ms = 0
        self.files_scanned = 0
        self.def_index = {}
        target_path = Path(directory)
        if not target_path.is_dir():
            return spans

        for root, dirs, files in os.walk(directory, followlinks=False):
            dirs[:] = [
                d for d in dirs
                if d not in _SKIP_DIRS and not d.startswith(".")
            ]
            for file in sorted(files):
                if file.endswith(".py"):
                    py_path = os.path.join(root, file)
                    self.files_scanned += 1
                    new_spans, cursor_ms = self._parse_file(py_path, cursor_ms)
                    spans.extend(new_spans)
        return spans

    def _parse_file(self, file_path: str, cursor_ms: int):
        try:
            source = Path(file_path).read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(source)
        except (OSError, SyntaxError, ValueError):
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
        # (start, end, is_async, name) for every function - innermost enclosing
        # function decides whether a call runs on the event loop.
        self._funcs = [
            (n.lineno, getattr(n, "end_lineno", n.lineno),
             isinstance(n, ast.AsyncFunctionDef), n.name)
            for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._absorb_def(node.name, _classify_function_def(node))

        spans: list[Span] = []

        for node in ast.walk(tree):
            # Synchronous blocking I/O - flagged anywhere.
            if isinstance(node, ast.Call):
                spans_here, cursor_ms = self._blocking_io(node, cursor_ms)
                spans.extend(spans_here)
                spans_here, cursor_ms = self._client_init(node, cursor_ms)
                spans.extend(spans_here)

            # LLM calls + sequential independent work - scoped per function.
            if isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
                spans_here, cursor_ms = self._scan_function(node, cursor_ms)
                spans.extend(spans_here)

        return spans, cursor_ms

    def _enclosing_func(self, lineno: int):
        """Innermost (start, end, is_async, name) containing lineno, or None."""
        best = None
        for f in self._funcs:
            if f[0] <= lineno <= f[1] and (best is None or f[0] >= best[0]):
                best = f
        return best

    def _snippet(self, node: ast.AST) -> str:
        seg = ast.get_source_segment(self._source, node)
        return seg.strip() if seg else ""

    def _blocking_io(self, node: ast.Call, cursor_ms: int):
        # Awaited calls run on the event loop asynchronously - not blocking.
        if id(node) in self._awaited_calls:
            return [], cursor_ms
        call_name = _node_name(node.func)
        line = getattr(node, "lineno", 0)
        enclosing = self._enclosing_func(line)
        in_async = bool(enclosing and enclosing[2])

        def emit(span_type: str, duration_ms: int, kind: str):
            span, cur = _make_span(
                name=f"{call_name}@{self._file}:{line}",
                span_type=span_type, cursor_ms=cursor_ms, duration_ms=duration_ms,
                metadata={"async": False, "kind": kind, "in_async": in_async,
                          "code": self._snippet(node),
                          "file": self._file, "line": line},
            )
            return [span], cur

        if call_name in _SYNC_HTTP:
            return emit("api_call", 500, "http")
        if call_name in _SYNC_DB:
            return emit("db_query", 200, "db")
        if in_async and (call_name in _SYNC_CLOUD_CALLS or _terminal(call_name) in _SYNC_CLOUD_TERMINALS):
            return emit("api_call", 600, "cloud")
        # sleep / subprocess are only latency bugs when they run on the event
        # loop - in plain sync code they're normal, so don't flag them there.
        if in_async and call_name in _SYNC_SLEEP:
            return emit("api_call", 1000, "sleep")
        if in_async and call_name in _SYNC_SUBPROC:
            return emit("api_call", 800, "subprocess")
        return [], cursor_ms

    def _client_init(self, node: ast.Call, cursor_ms: int):
        """Flag API-client construction inside an ordinary (per-request)
        function - connection/TLS setup should happen once at startup."""
        call_name = _node_name(node.func)
        if call_name not in _CLIENT_CTORS:
            return [], cursor_ms
        line = getattr(node, "lineno", 0)
        enclosing = self._enclosing_func(line)
        if enclosing is None:
            return [], cursor_ms          # module level = startup, fine
        fname = enclosing[3].lower()
        if any(tok in fname for tok in _INIT_NAME_TOKENS):
            return [], cursor_ms          # an init/factory path, expected
        span, cursor_ms = _make_span(
            name=f"{call_name}@{self._file}:{line}",
            span_type="client_init", cursor_ms=cursor_ms, duration_ms=300,
            metadata={"code": self._snippet(node), "ctor": call_name,
                      "func": enclosing[3], "file": self._file, "line": line},
        )
        return [span], cursor_ms

    def _scan_function(self, func: ast.AST, cursor_ms: int):
        """Emit LLM-call spans and groups of genuinely-independent awaited calls."""
        spans: list[Span] = []

        # 1. LLM calls in this function.
        for n in ast.walk(func):
            if isinstance(n, ast.Await) and isinstance(n.value, ast.Call):
                call_name = _node_name(n.value.func)
                if _is_llm_call(call_name):
                    streaming = _is_streaming(n.value, call_name)
                    # If args are forwarded via **kwargs we can't see stream=...
                    # directly - but try to resolve it from the same function first.
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
                                  "prompt_hash": _static_prompt_hash(n.value),
                                  "code": self._snippet(n), "file": self._file,
                                  "line": line, "call": call_name},
                    )
                    spans.append(span)

        # 2. Sequential independent awaited assignments, block-scoped.
        for block in self._statement_blocks(func):
            groups = self._independent_runs(block)
            for group in groups:
                gid = f"g{next(_GROUP_ID_COUNTER)}"
                for stmt in group:
                    call = stmt.value.value  # Assign or AnnAssign -> Await -> Call
                    line = getattr(stmt, "lineno", 0)
                    span, cursor_ms = _make_span(
                        name=_node_name(call.func) or f"tool@{line}",
                        span_type="tool_call", cursor_ms=cursor_ms, duration_ms=400,
                        metadata={"group_id": gid, "code": self._snippet(stmt),
                                  "call_src": self._snippet(call),
                                  "targets": [_target_str(stmt)],
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
        def is_candidate(stmt) -> ast.stmt | None:
            if isinstance(stmt, ast.Assign):
                if (isinstance(stmt.value, ast.Await)
                        and isinstance(stmt.value.value, ast.Call)):
                    call_name = _node_name(stmt.value.value.func)
                    if _terminal(call_name) in _ORDERED_TERMINALS:
                        return None
                    return stmt
            elif isinstance(stmt, ast.AnnAssign):
                if (stmt.value and isinstance(stmt.value, ast.Await)
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
