#!/usr/bin/env bash
#
# Relay MCP — dev runner (macOS / Linux / Git Bash)
#
# Usage:
#   ./run.sh install        Install the relay-mcp package in editable mode
#   ./run.sh register       Add relay to ~/.claude/claude_code_config.json
#   ./run.sh test [DIR]     Run the audit engine directly on DIR (default: .)
#   ./run.sh serve          Start the MCP server in the foreground (stdio; debug)
#   ./run.sh all            install + register
#
# Env:
#   RELAY_API_KEY   API key used for register/test/serve

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG="$HOME/.claude/claude_code_config.json"
PY="${PYTHON:-python3}"

install_pkg() {
  echo "==> pip install -e ."
  (cd "$ROOT" && "$PY" -m pip install -e .)
}

register_mcp() {
  echo "==> Registering 'relay' in $CONFIG"
  mkdir -p "$(dirname "$CONFIG")"
  local key="${RELAY_API_KEY:-your_key_here}"
  [ -f "$CONFIG" ] || echo '{}' > "$CONFIG"

  RELAY_KEY="$key" CONFIG="$CONFIG" "$PY" - <<'PYEOF'
import json, os
cfg_path = os.environ["CONFIG"]
with open(cfg_path) as f:
    cfg = json.load(f) or {}
cfg.setdefault("mcpServers", {})
cfg["mcpServers"]["relay"] = {
    "command": "relay-mcp",
    "env": {"RELAY_API_KEY": os.environ["RELAY_KEY"]},
}
with open(cfg_path, "w") as f:
    json.dump(cfg, f, indent=2)
print("wrote", cfg_path)
PYEOF

  echo "Done. Restart Claude Code, then say: 'Audit this codebase for latency issues'"
  [ "$key" = "your_key_here" ] && echo "NOTE: set RELAY_API_KEY and re-run, or edit the key in $CONFIG"
}

test_audit() {
  local target="${1:-.}"
  local abs; abs="$(cd "$target" && pwd)"
  echo "==> Running audit engine on: $abs"
  (cd "$ROOT" && "$PY" -c "from mcp_server.engine.engine import AuditEngine; import json; r=AuditEngine().run_on_codebase('$abs'); print(json.dumps(r.to_dict(), indent=2, default=str))")
}

serve() {
  echo "==> Starting MCP server (stdio). Ctrl+C to stop."
  (cd "$ROOT" && "$PY" -m mcp_server.server)
}

case "${1:-help}" in
  install)  install_pkg ;;
  register) register_mcp ;;
  test)     test_audit "${2:-.}" ;;
  serve)    serve ;;
  all)      install_pkg; register_mcp ;;
  *)
    echo "Relay MCP dev runner"
    echo "  ./run.sh install      Install package (pip install -e .)"
    echo "  ./run.sh register     Add to Claude Code config"
    echo "  ./run.sh all          install + register"
    echo "  ./run.sh test [DIR]   Audit a directory directly (no MCP)"
    echo "  ./run.sh serve        Run MCP server in foreground (debug)"
    ;;
esac
