import ast
import os
import uuid
from pathlib import Path
from mcp_server.engine.base_detector import CodeSpan

SKIP_DIRS = {"venv", ".venv", "__pycache__", ".git", "node_modules", ".pytest_cache"}

LLM_CALL_ATTRS = {
    "completions.create", "messages.create", "generate",
    "ainvoke", "invoke", "arun", "run", "acomplete", "complete",
}

TOOL_PATTERNS = {"@tool", "StructuredTool", "FunctionTool"}

SYNC_HTTP_CALLS = {
    ("requests", "get"), ("requests", "post"), ("requests", "put"),
    ("requests", "delete"), ("requests", "patch"),
    ("httpx", "get"), ("httpx", "post"), ("httpx", "put"),
    ("httpx", "delete"),
}

DB_CALL_ATTRS = {
    "execute", "executemany", "find", "find_one", "insert_one",
    "insert_many", "update_one", "update_many", "delete_one", "delete_many",
}


def _attr_chain(node) -> str:
    """Return dotted attribute chain for a node, e.g. 'client.messages.create'."""
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return ".".join(reversed(parts))


class CodeParser:
    """Parses Python agent codebases using AST analysis."""

    def parse_directory(self, directory: str) -> list[CodeSpan]:
        spans = []
        path = Path(directory)
        for py_file in path.rglob("*.py"):
            if any(skip in py_file.parts for skip in SKIP_DIRS):
                continue
            spans.extend(self.parse_file(str(py_file)))
        return spans

    def parse_file(self, file_path: str) -> list[CodeSpan]:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                source = f.read()
        except OSError:
            return []

        try:
            tree = ast.parse(source)
        except SyntaxError:
            return []

        return self._extract_spans(tree, source, file_path)

    def _extract_spans(self, tree: ast.AST, source: str, file_path: str) -> list[CodeSpan]:
        spans = []
        lines = source.split("\n")

        # Collect decorated functions to detect @tool
        tool_decorated_lines: set[int] = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for decorator in node.decorator_list:
                    dname = _attr_chain(decorator)
                    if dname in ("tool",) or any(p in dname for p in TOOL_PATTERNS):
                        tool_decorated_lines.add(node.lineno)

        for node in ast.walk(tree):
            if isinstance(node, ast.Await):
                span = self._analyze_await(node, lines, file_path)
                if span:
                    spans.append(span)
            elif isinstance(node, ast.Call):
                span = self._analyze_call(node, lines, file_path)
                if span:
                    spans.append(span)

        # Add agent_loop spans for init/setup functions
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                name_lower = node.name.lower()
                if any(kw in name_lower for kw in ("init", "setup", "connect", "startup")):
                    lineno = node.lineno
                    spans.append(CodeSpan(
                        id=str(uuid.uuid4()),
                        name=node.name,
                        file_path=file_path,
                        line_number=lineno,
                        span_type="agent_loop",
                        pattern=lines[lineno - 1].strip() if lineno <= len(lines) else "",
                        metadata={},
                        start_ms=lineno * 10,
                        end_ms=lineno * 10 + 600,
                        duration_ms=600,
                    ))

        return spans

    def _analyze_await(self, node: ast.Await, lines: list[str], file_path: str) -> CodeSpan | None:
        lineno = getattr(node, "lineno", 0)
        call = node.value
        if not isinstance(call, ast.Call):
            return None

        chain = _attr_chain(call.func)
        span_type, metadata, duration_ms = self._classify_call(chain, is_async=True)

        if span_type is None:
            return None

        pattern = lines[lineno - 1].strip() if lineno and lineno <= len(lines) else chain

        return CodeSpan(
            id=str(uuid.uuid4()),
            name=chain.split(".")[-1] if "." in chain else chain,
            file_path=file_path,
            line_number=lineno,
            span_type=span_type,
            pattern=pattern,
            metadata=metadata,
            start_ms=lineno * 10,
            end_ms=lineno * 10 + duration_ms,
            duration_ms=duration_ms,
        )

    def _analyze_call(self, node: ast.Call, lines: list[str], file_path: str) -> CodeSpan | None:
        lineno = getattr(node, "lineno", 0)
        chain = _attr_chain(node.func)

        # Detect StructuredTool / FunctionTool instantiation
        func_name = chain.split(".")[-1] if chain else ""
        if func_name in ("StructuredTool", "FunctionTool"):
            pattern = lines[lineno - 1].strip() if lineno and lineno <= len(lines) else chain
            return CodeSpan(
                id=str(uuid.uuid4()),
                name=func_name,
                file_path=file_path,
                line_number=lineno,
                span_type="tool_call",
                pattern=pattern,
                metadata={},
                start_ms=lineno * 10,
                end_ms=lineno * 10 + 30,
                duration_ms=30,
            )

        # Detect sync HTTP calls (requests.get, httpx.get, etc.)
        parts = chain.split(".")
        if len(parts) >= 2:
            module, method = parts[0], parts[-1]
            if (module, method) in SYNC_HTTP_CALLS:
                pattern = lines[lineno - 1].strip() if lineno and lineno <= len(lines) else chain
                return CodeSpan(
                    id=str(uuid.uuid4()),
                    name=chain,
                    file_path=file_path,
                    line_number=lineno,
                    span_type="api_call",
                    pattern=pattern,
                    metadata={"async": False},
                    start_ms=lineno * 10,
                    end_ms=lineno * 10 + 200,
                    duration_ms=200,
                )

        # Detect sync DB calls (session.execute, collection.find, etc.)
        if func_name in DB_CALL_ATTRS and "async" not in chain.lower():
            pattern = lines[lineno - 1].strip() if lineno and lineno <= len(lines) else chain
            return CodeSpan(
                id=str(uuid.uuid4()),
                name=chain,
                file_path=file_path,
                line_number=lineno,
                span_type="db_query",
                pattern=pattern,
                metadata={"async": False},
                start_ms=lineno * 10,
                end_ms=lineno * 10 + 200,
                duration_ms=200,
            )

        return None

    def _classify_call(self, chain: str, is_async: bool) -> tuple[str | None, dict, int]:
        """Return (span_type, metadata, duration_ms) for a call chain."""
        last = chain.split(".")[-1] if "." in chain else chain

        # LLM calls
        if any(pat in chain for pat in LLM_CALL_ATTRS):
            # Check for streaming keyword presence heuristic
            # We can't see keyword args here, so default to non-streaming (pessimistic)
            return "llm_call", {"streaming": False}, 2500

        # Tool calls
        if last in ("run", "arun") and "tool" in chain.lower():
            return "tool_call", {}, 100

        # DB queries
        if last in DB_CALL_ATTRS:
            is_db_async = chain.startswith("await") or is_async
            return "db_query", {"async": is_db_async}, 150

        # HTTP calls (async versions — httpx.AsyncClient)
        if "AsyncClient" in chain or "aiohttp" in chain:
            return "api_call", {"async": True}, 150

        return None, {}, 50
