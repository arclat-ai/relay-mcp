"""
Verification pass.

`scan` (the detectors) is a structural stage: it flags *candidate* patterns.
`verify` is a semantic stage: it re-reads each flagged site in context and
decides whether the candidate is a real, actionable latency gap or a false
positive - and, when it dismisses one, says why in one line.

The heuristics here are deliberately conservative and explainable. They encode
the manual checks a reviewer does:

  * a blocking I/O call inside a *synchronous* function is a batch/util call,
    not something stalling an event loop;
  * a non-streaming LLM call in a `run_inference` / summary / classify helper,
    or one returning structured JSON, is non-streamable by design and off the
    spoken-turn hot path;
  * a run of awaited calls whose targets are ordered emits / queue ops must stay
    ordered - parallelizing them changes behaviour;
  * a "parallelize these awaits" suggestion is worthless if one branch does no
    I/O - gathering an expensive call with an in-memory lookup saves nothing.
    We resolve each awaited callee in the codebase and check whether it is
    provably cheap (no await, no I/O in its body). Cost, not call count.

This is heuristic, not a proof. Anything it cannot confidently dismiss it marks
`confirmed` so a human still looks - including two genuinely expensive calls,
which are a real gather win. Impact is annotated so cold-path survivors don't
masquerade as per-turn wins.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any

_SKIP_DIRS = {"venv", ".venv", "__pycache__", ".git", "node_modules", "tests",
              "test", "examples", "docs", ".mypy_cache"}

_UTILITY_NAME = re.compile(
    r"(run_inference|generate_reply|summar|extract|classif|detect|"
    r"check_for|voicemail|judge|title|language|moderat|embed|rerank|rank)",
    re.I,
)
_STRUCTURED = ("request_json", "response_format", "json.loads", "json_object",
               "output_text", '"stream": false', "stream=false")
_ORDERED = {
    "send", "send_nowait", "write", "emit", "publish", "flush", "close", "commit",
    "ack", "push", "push_frame", "push_error", "put", "get", "release", "acquire",
    "drain", "join", "seek", "connect", "disconnect", "start", "stop",
}

# Tokens that mark a function body as doing real I/O (=> not cheap).
_IO_MODULES = {"requests", "httpx", "aiohttp", "urllib", "socket", "subprocess",
               "sqlite3", "psycopg", "psycopg2", "asyncpg", "aiofiles", "boto3",
               "redis", "pymongo", "smtplib", "ftplib"}
_IO_METHODS = {"post", "put", "delete", "patch", "request", "execute", "read",
               "write", "recv", "sendall", "fetch", "query", "download",
               "upload", "aread", "aiter_lines"}
_IO_BUILTINS = {"open"}

# Callee cost classes
IO, CHEAP, UNKNOWN = "io", "cheap", "unknown"


def _terminal(call_name: str) -> str:
    return call_name.rsplit(".", 1)[-1].rstrip("(") if call_name else ""


def _strip_docstring(body: list[ast.stmt]) -> list[ast.stmt]:
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
            and isinstance(body[0].value.value, str):
        return body[1:]
    return body


def _is_stub(node) -> bool:
    body = _strip_docstring(node.body)
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


def _classify_def(node) -> str:
    """Cost class of a single function definition."""
    if _is_stub(node):
        return UNKNOWN
    for n in ast.walk(node):
        if isinstance(n, ast.Await):
            return IO
        if isinstance(n, ast.Name) and n.id in _IO_MODULES:
            return IO
        if isinstance(n, ast.Call):
            fn = n.func
            if isinstance(fn, ast.Name) and fn.id in _IO_BUILTINS:
                return IO
            if isinstance(fn, ast.Attribute) and fn.attr in _IO_METHODS:
                return IO
    return CHEAP


def _enclosing_function(tree: ast.AST, lineno: int) -> ast.AST | None:
    best = None
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            start = node.lineno
            end = getattr(node, "end_lineno", start)
            if start <= lineno <= end and (best is None or start >= best.lineno):
                best = node
    return best


class _FileContext:
    def __init__(self, path: str):
        self.tree = None
        self.source = ""
        try:
            self.source = Path(path).read_text(encoding="utf-8", errors="ignore")
            self.tree = ast.parse(self.source)
        except (OSError, SyntaxError, ValueError):
            self.tree = None

    def func_at(self, lineno: int):
        if self.tree is None:
            return None, "", False
        fn = _enclosing_function(self.tree, lineno)
        if fn is None:
            return None, "", False
        seg = ast.get_source_segment(self.source, fn) or ""
        return fn, seg, isinstance(fn, ast.AsyncFunctionDef)


class _DefIndex:
    """Maps a function/method *name* to an aggregate cost class across the
    scanned codebase. IO dominates (if any definition does I/O, treat the name
    as I/O); otherwise CHEAP if any concrete definition is cheap; else UNKNOWN."""

    def __init__(self, target_dir: str | None):
        self._cls: dict[str, str] = {}
        if not target_dir:
            return
        root = Path(target_dir)
        if not root.is_dir():
            return
        for py in root.rglob("*.py"):
            if any(part in _SKIP_DIRS for part in py.parts):
                continue
            try:
                tree = ast.parse(py.read_text(encoding="utf-8", errors="ignore"))
            except (OSError, SyntaxError, ValueError):
                continue
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    self._absorb(node.name, _classify_def(node))

    def _absorb(self, name: str, cls: str) -> None:
        cur = self._cls.get(name)
        if cur == IO or cls == IO:
            self._cls[name] = IO
        elif cur == CHEAP or cls == CHEAP:
            self._cls[name] = CHEAP
        else:
            self._cls[name] = UNKNOWN

    def cost(self, name: str) -> str:
        return self._cls.get(name, UNKNOWN)


def _resolve_file(raw: str) -> str:
    if not raw:
        return ""
    m = re.search(r"([A-Za-z]:[\\/][^@]*?\.py|/[^@]*?\.py|[^@\s]+\.py)", raw)
    return m.group(1) if m else ""


def _awaited_terminals(code_before: str) -> list[str]:
    return [_terminal(m.group(1))
            for m in re.finditer(r"await\s+([A-Za-z_][\w\.]*)\s*\(", code_before or "")]


def _classify(finding: dict[str, Any], ctx_cache: dict[str, _FileContext],
              defs: _DefIndex) -> dict[str, str]:
    ftype = finding.get("type", "")
    file = finding.get("file") or ""
    lines = finding.get("lines") or []
    loc = finding.get("location")
    disp = loc.get("display") if isinstance(loc, dict) else (loc or "")
    if not file:
        file = (loc.get("file") if isinstance(loc, dict) else "") or _resolve_file(disp)
    lineno = lines[0] if lines else 0
    ctx = None
    if file and Path(file).is_file():
        ctx = ctx_cache.get(file) or ctx_cache.setdefault(file, _FileContext(file))

    if ftype == "blocking_io":
        if ctx and lineno:
            _, _, is_async = ctx.func_at(lineno)
            if not is_async:
                return _d("synchronous batch API - off the async path")
        return _c("blocks the event loop in an async path", impact="high")

    if ftype == "sync_output":
        if ctx and lineno:
            fn, seg, _ = ctx.func_at(lineno)
            name = getattr(fn, "name", "") if fn else ""
            low = seg.lower()
            if name and _UTILITY_NAME.search(name):
                return _d("utility call - off the voice hot path")
            if any(tok in low for tok in _STRUCTURED):
                return _d("structured/JSON output - not streamable")
            if "yield" in low:
                return _d("streaming set upstream - not the returned path")
        # No dismissal evidence. If streaming is *known* to be off (severity
        # high, not a **kwargs guess), keep it; a guess stays dismissed.
        if str(finding.get("severity", "")).lower() == "high":
            return _c("full completion awaited before first token", impact="medium")
        return _d("streaming state unknown (**kwargs) - unconfirmed")

    if ftype == "sequential_tools":
        terminals = _awaited_terminals(finding.get("code_before", ""))
        if not terminals:
            for tok in re.split(r"[,\s]+", disp if isinstance(disp, str) else ""):
                t = _terminal(tok)
                if t:
                    terminals.append(t)
        if set(terminals) & _ORDERED:
            return _d("ordered emits / queue ops - must stay sequential")
        # cost-aware: if a branch provably does no I/O, gathering saves nothing.
        cheap = next((t for t in terminals if defs.cost(t) == CHEAP), None)
        if cheap:
            return _d(f"one branch ({cheap}) is in-memory - nothing to parallelize")
        return _c("independent awaits - gather-able", impact="low")

    # ---- cold_start (per-request client construction) ---------------------
    if ftype == "cold_start":
        return _c("client constructed per call - hoist to startup", impact="medium")

    # ---- cache_miss (repeated fully-static LLM call) ----------------------
    if ftype == "cache_miss":
        return _c("identical static input at multiple sites - cacheable", impact="medium")

    # ---- no_prefetch ------------------------------------------------------
    if ftype == "no_prefetch":
        return _c("stable call pair - speculative prefetch possible", impact="low")

    return _c("no dismissal rule matched", impact="unknown")


def _d(reason: str) -> dict[str, str]:
    return {"status": "dismissed", "reason": reason, "impact": "none"}


def _c(reason: str, impact: str = "unknown") -> dict[str, str]:
    return {"status": "confirmed", "reason": reason, "impact": impact}


def verify_findings(findings: list[dict[str, Any]],
                    target_dir: str | None = None) -> dict[str, Any]:
    """Return {findings: [...+status/reason/impact], summary: {...}}.

    target_dir enables cost-aware dismissal (resolving awaited callees across the
    scanned codebase). Without it, `parallelize` findings fall back to structural
    checks only.
    """
    ctx_cache: dict[str, _FileContext] = {}
    defs = _DefIndex(target_dir)
    out: list[dict[str, Any]] = []
    confirmed = high = 0
    for f in findings:
        verdict = _classify(f, ctx_cache, defs)
        g = dict(f)
        g.update(verdict)
        out.append(g)
        if verdict["status"] == "confirmed":
            confirmed += 1
            if verdict["impact"] == "high":
                high += 1
    return {
        "findings": out,
        "summary": {
            "flagged": len(findings),
            "confirmed": confirmed,
            "dismissed": len(findings) - confirmed,
            "confirmed_high_impact": high,
        },
    }
