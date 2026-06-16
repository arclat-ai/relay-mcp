"""
Parses Python agent codebases using AST analysis.
Produces Span objects with synthetic timing so the existing detectors work unchanged.
"""
import ast
import uuid
from pathlib import Path
from typing import List

from mcp_server.engine.base_detector import Span

_SKIP_DIRS = {"venv", ".venv", "__pycache__", ".git", "node_modules", ".mypy_cache"}

_LLM_METHODS = {
    "completions.create", "messages.create", "generate",
    "ainvoke", "invoke", "arun", "run",
}
_TOOL_DECORATORS = {"tool", "StructuredTool", "FunctionTool"}
_SYNC_HTTP = {"requests.get", "requests.post", "requests.put", "requests.delete",
              "httpx.get", "httpx.post"}
_SYNC_DB = {"session.execute", "cursor.execute", "collection.find", "conn.execute"}
_INIT_KEYWORDS = ("__init__", "setup", "connect", "initialize")


def _node_name(node: ast.expr) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{_node_name(node.value)}.{node.attr}"
    return ""


def _make_span(name: str, span_type: str, cursor_ms: int, duration_ms: int, metadata: dict) -> tuple[Span, int]:
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
        for py_file in sorted(Path(directory).rglob("*.py")):
            if any(part in _SKIP_DIRS for part in py_file.parts):
                continue
            new_spans, cursor_ms = self._parse_file(str(py_file), cursor_ms)
            spans.extend(new_spans)
        return spans

    def _parse_file(self, file_path: str, cursor_ms: int) -> tuple[List[Span], int]:
        try:
            source = Path(file_path).read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(source)
        except SyntaxError:
            return [], cursor_ms

        spans: List[Span] = []
        rel = file_path

        for node in ast.walk(tree):
            # Detect async LLM calls (await client.messages.create / completions.create)
            if isinstance(node, ast.Await) and isinstance(node.value, ast.Call):
                call_name = _node_name(node.value.func)
                is_llm = any(pat in call_name for pat in _LLM_METHODS)
                if is_llm:
                    # Check if stream=True keyword arg present
                    streaming = any(
                        (isinstance(kw.value, ast.Constant) and kw.value.value is True)
                        for kw in node.value.keywords
                        if kw.arg == "stream"
                    )
                    span, cursor_ms = _make_span(
                        name=f"{rel}:{getattr(node, 'lineno', 0)}",
                        span_type="llm_call",
                        cursor_ms=cursor_ms,
                        duration_ms=500 if streaming else 3000,
                        metadata={"streaming": streaming},
                    )
                    spans.append(span)

            # Detect sequential awaited function calls in function bodies
            if isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
                awaits_in_body = [
                    n for n in ast.walk(node)
                    if isinstance(n, ast.Expr)
                    and isinstance(n.value, ast.Await)
                    and isinstance(n.value.value, ast.Call)
                    and not any(pat in _node_name(n.value.value.func) for pat in _LLM_METHODS)
                ]
                if len(awaits_in_body) >= 2:
                    for aw in awaits_in_body:
                        call_name = _node_name(aw.value.value.func)
                        span, cursor_ms = _make_span(
                            name=call_name or f"tool@{getattr(aw, 'lineno', 0)}",
                            span_type="tool_call",
                            cursor_ms=cursor_ms,
                            duration_ms=400,
                            metadata={},
                        )
                        spans.append(span)

            # Detect synchronous HTTP calls (blocking)
            if isinstance(node, ast.Call):
                call_name = _node_name(node.func)
                if call_name in _SYNC_HTTP:
                    span, cursor_ms = _make_span(
                        name=f"{call_name}@{rel}:{getattr(node, 'lineno', 0)}",
                        span_type="api_call",
                        cursor_ms=cursor_ms,
                        duration_ms=500,
                        metadata={"async": False},
                    )
                    spans.append(span)
                elif call_name in _SYNC_DB:
                    span, cursor_ms = _make_span(
                        name=f"{call_name}@{rel}:{getattr(node, 'lineno', 0)}",
                        span_type="db_query",
                        cursor_ms=cursor_ms,
                        duration_ms=200,
                        metadata={"async": False},
                    )
                    spans.append(span)

            # Detect __init__ / setup methods as cold-start candidates
            if isinstance(node, ast.FunctionDef) and any(kw in node.name for kw in _INIT_KEYWORDS):
                span, cursor_ms = _make_span(
                    name=node.name,
                    span_type="agent_loop",
                    cursor_ms=cursor_ms,
                    duration_ms=600,
                    metadata={},
                )
                spans.append(span)

        return spans, cursor_ms
