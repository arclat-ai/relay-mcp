"""
Verification pass.

`scan` (the detectors) is a structural stage: it flags *candidate* patterns.
`verify` is a semantic stage: it re-reads each flagged site in context and
decides whether the candidate is a real, actionable latency gap or a false
positive — and, when it dismisses one, says why in one line.

The heuristics here are deliberately conservative and explainable. They encode
the manual checks a reviewer does:

  * a blocking I/O call inside a *synchronous* function is a batch/util call,
    not something stalling an event loop;
  * a non-streaming LLM call in a `run_inference` / summary / classify / detect
    helper (or one returning structured JSON) is non-streamable by design and
    off the spoken-turn hot path;
  * a run of awaited calls whose targets are ordered emits / queue ops must stay
    ordered — parallelizing them changes behavior.

This is heuristic, not a proof. Anything it cannot confidently dismiss it marks
`confirmed` so a human still looks. Impact is annotated so cold-path survivors
don't masquerade as per-turn wins.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

# Enclosing-function name patterns that indicate an off-hot-path utility call
# (summaries, classification, endpoint checks) rather than the spoken turn.
_UTILITY_NAME = re.compile(
    r"(run_inference|generate_reply|summar|extract|classif|detect|"
    r"check_for|voicemail|judge|title|language|moderat|embed|rerank|rank)",
    re.I,
)

# Tokens in a function body that mean the LLM output is consumed whole
# (structured / JSON) and therefore cannot be streamed token-by-token.
_STRUCTURED = ("request_json", "response_format", "json.loads", "json_object",
               "output_text", '"stream": false', "stream=false")

# Call terminals whose ordering matters — never independently parallelizable.
_ORDERED = {
    "send", "send_nowait", "write", "emit", "publish", "flush", "close", "commit",
    "ack", "push", "push_frame", "push_error", "put", "get", "release", "acquire",
    "drain", "join", "seek", "connect", "disconnect", "start", "stop",
}


def _terminal(call_name: str) -> str:
    return call_name.rsplit(".", 1)[-1].rstrip("(") if call_name else ""


def _enclosing_function(tree: ast.AST, lineno: int) -> Optional[ast.AST]:
    """Innermost FunctionDef/AsyncFunctionDef whose span contains lineno."""
    best = None
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            start = node.lineno
            end = getattr(node, "end_lineno", start)
            if start <= lineno <= end:
                if best is None or start >= best.lineno:
                    best = node
    return best


class _FileContext:
    """Lazily parsed AST + source for a single file, cached per verify run."""

    def __init__(self, path: str):
        self.path = path
        self.tree: Optional[ast.AST] = None
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


def _resolve_file(raw: str) -> str:
    # locations arrive as "call@C:\path.py:line" or "C:\path.py:line-line" or a dict display
    if not raw:
        return ""
    m = re.search(r"([A-Za-z]:[\\/][^@]*?\.py|/[^@]*?\.py|[^@\s]+\.py)", raw)
    return m.group(1) if m else ""


def _classify(finding: Dict[str, Any], ctx_cache: Dict[str, _FileContext]) -> Dict[str, str]:
    ftype = finding.get("type", "")
    file = finding.get("file") or ""
    lines = finding.get("lines") or []
    if not file:
        loc = finding.get("location")
        disp = loc.get("display") if isinstance(loc, dict) else (loc or "")
        file = (loc.get("file") if isinstance(loc, dict) else "") or _resolve_file(disp)
    lineno = lines[0] if lines else 0

    ctx = None
    if file and Path(file).is_file():
        ctx = ctx_cache.get(file) or ctx_cache.setdefault(file, _FileContext(file))

    # ---- blocking_io -------------------------------------------------------
    if ftype == "blocking_io":
        if ctx and lineno:
            _, _, is_async = ctx.func_at(lineno)
            if not is_async:
                return _d("synchronous batch API — off the async path")
        return _c("blocks the event loop in an async path", impact="high")

    # ---- sync_output (streaming) ------------------------------------------
    if ftype == "sync_output":
        if ctx and lineno:
            fn, seg, _ = ctx.func_at(lineno)
            name = getattr(fn, "name", "") if fn else ""
            low = seg.lower()
            if name and _UTILITY_NAME.search(name):
                return _d("utility call — off the voice hot path")
            if any(tok in low for tok in _STRUCTURED):
                return _d("structured/JSON output — not streamable")
            if "yield" in low:
                # inside a generator: the spoken path streams; the flagged
                # create forwards **kwargs whose stream is set upstream
                return _d("streaming set upstream — not the returned path")
        return _d("non-streaming helper — unconfirmed on hot path")

    # ---- sequential_tools (parallelize) -----------------------------------
    if ftype == "sequential_tools":
        blob = finding.get("code_before", "") or ""
        disp = ""
        loc = finding.get("location")
        if isinstance(loc, dict):
            disp = loc.get("display", "")
        terminals = set()
        for m in re.finditer(r"await\s+([\w\.]+)\s*\(", blob):
            terminals.add(_terminal(m.group(1)))
        for tok in re.split(r"[,\s]+", disp):
            terminals.add(_terminal(tok))
        if terminals & _ORDERED:
            return _d("ordered emits / queue ops — must stay sequential")
        # independent but the calls are the same helper on different vars:
        # gather-able yet usually trivial. Confirm as low-impact.
        return _c("independent awaits — gather-able", impact="low")

    return _c("no dismissal rule matched", impact="unknown")


def _d(reason: str) -> Dict[str, str]:
    return {"status": "dismissed", "reason": reason, "impact": "none"}


def _c(reason: str, impact: str = "unknown") -> Dict[str, str]:
    return {"status": "confirmed", "reason": reason, "impact": impact}


def verify_findings(findings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Return {findings: [...+status/reason/impact], summary: {...}}."""
    ctx_cache: Dict[str, _FileContext] = {}
    out: List[Dict[str, Any]] = []
    confirmed = 0
    high = 0
    for f in findings:
        verdict = _classify(f, ctx_cache)
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
