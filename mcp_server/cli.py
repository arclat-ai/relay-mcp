"""
`relay` command-line interface.

    relay scan   <dir>     structural pass - flag candidate latency patterns
    relay verify <dir>     semantic pass  - trace each flag, keep only real gaps
    relay report <dir>     write relay-report.json for the dashboard
    relay mcp              run the MCP server (same as `relay-mcp`)

`scan` and `verify` accept --json for machine-readable output.
`verify` accepts --fail-on {none,high,any} to exit non-zero as a CI gate.

`scan` and `verify` share the AST engine used by the MCP tools, so the CLI and
the agent-facing tools never diverge.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

from mcp_server.engine.engine import AuditEngine

# Prefer UTF-8 so the marks/arrows render; fall back to ASCII on legacy consoles.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
_UNI = (getattr(sys.stdout, "encoding", "") or "").lower().startswith("utf")
MARK_X = "✗" if _UNI else "x"
MARK_OK = "✓" if _UNI else "OK"
MARK_DOT = "●" if _UNI else "*"
ARROW = "→" if _UNI else "->"
ELL = "…" if _UNI else "..."

# ---- tiny ANSI helper (no deps) ----
_TTY = sys.stdout.isatty()
def _c(code: str, s: str) -> str:
    return f"\033[{code}m{s}\033[0m" if _TTY else s
DIM = lambda s: _c("2", s)
BOLD = lambda s: _c("1", s)
GREEN = lambda s: _c("32", s)
AMBER = lambda s: _c("33", s)
RED = lambda s: _c("31", s)
CYAN = lambda s: _c("36", s)


def _short(loc) -> str:
    disp = loc.get("display") if isinstance(loc, dict) else (loc or "")
    disp = re.sub(r".*[\\/](?=[^\\/]+[\\/][^\\/]+\.py)", "", str(disp))
    return disp.replace("\\", "/")


def _scan(target: str):
    result = AuditEngine().run_on_codebase(target)
    return result.to_dict()


def cmd_scan(args) -> int:
    rd = _scan(args.directory)
    b = rd["bottlenecks"]
    if getattr(args, "json", False):
        print(json.dumps(rd, indent=2))
        return 0
    print(f"{GREEN('$')} {BOLD('relay scan')} {args.directory}")
    print(DIM(f"scanning {rd['files_scanned']} files{ELL}\n"))
    from collections import Counter
    by = Counter(x["type"] for x in b)
    for t, n in by.most_common():
        print(f"  {AMBER(str(n).rjust(4))}  {t}")
    print()
    print(f"  {AMBER(str(len(b)))} candidates flagged  {DIM('# raw pattern matches, unverified')}")
    return 0


def cmd_verify(args) -> int:
    rd = _scan(args.directory)
    # The engine already ran the verify pass - verdicts are nested per finding.
    v = {
        "findings": [dict(f, **f["verification"]) for f in rd["bottlenecks"]],
        "summary": rd["verification"],
    }
    s = v["summary"]
    if getattr(args, "json", False):
        print(json.dumps(rd, indent=2))
        return 0
    print(f"{GREEN('$')} {BOLD('relay verify')} {args.directory}")
    print(DIM(f"tracing each flag against runtime{ELL}\n"))
    for g in v["findings"]:
        if g["status"] == "dismissed":
            claim = g["title"].lower().replace(" independent tool calls", " awaits").replace(" output", "")
            print(f"  {RED(MARK_X)} {claim[:24].ljust(24)} {DIM(ARROW + ' ' + g['reason'])}")
    print()
    for g in v["findings"]:
        if g["status"] == "confirmed":
            tag = RED("HIGH") if g["impact"] == "high" else AMBER(g["impact"].upper())
            print(f"  {CYAN(MARK_DOT)} [{tag}] {g['title']}  {DIM(_short(g['location']))}")
            print(f"      {g['reason']}")
    print()
    flagged, dismissed = s["flagged"], s["dismissed"]
    if s["confirmed"] == 0:
        note = DIM(f"({flagged} flagged, all dismissed)")
        print(f"  {GREEN(MARK_OK)} {BOLD('0 real latency gaps')}   {note}")
    else:
        head = f"{s['confirmed']} confirmed ({s['confirmed_high_impact']} high-impact)"
        note = DIM(f"{dismissed} of {flagged} dismissed")
        print(f"  {CYAN('=')} {BOLD(head)}   {note}")

    # CI gate: exit non-zero when confirmed gaps remain, so `relay verify` can
    # fail a pipeline. Default `none` keeps the command informational.
    fail_on = getattr(args, "fail_on", "none")
    if fail_on == "high" and s["confirmed_high_impact"] > 0:
        return 1
    if fail_on == "any" and s["confirmed"] > 0:
        return 1
    return 0


def cmd_report(args) -> int:
    rd = _scan(args.directory)
    rd["generator"] = "relay-cli"
    rd["product"] = "relay"
    out = args.output or os.path.join(args.directory, "relay-report.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(rd, fh, indent=2)
    s = rd["verification"]
    print(f"{GREEN('$')} {BOLD('relay report')} {args.directory}")
    print(f"  {rd['summary']['total_bottlenecks']} findings "
          f"({s['confirmed']} confirmed, {s['dismissed']} dismissed)")
    print(f"  {GREEN(MARK_OK)} wrote {out}")
    print(DIM("  upload it at https://relay.arclat.com/dashboard"))
    return 0


def cmd_mcp(args) -> int:
    from mcp_server.server import main as _main
    _main()
    return 0


def main() -> int:
    p = argparse.ArgumentParser(prog="relay", description="Relay - AI voice/agent latency auditor")
    sub = p.add_subparsers(dest="cmd", required=True)

    ps = sub.add_parser("scan", help="flag candidate latency patterns")
    ps.add_argument("directory")
    ps.add_argument("--json", action="store_true", help="print the full report as JSON")
    ps.set_defaults(func=cmd_scan)

    pv = sub.add_parser("verify", help="trace flags; keep only real gaps")
    pv.add_argument("directory")
    pv.add_argument("--json", action="store_true", help="print the full report as JSON")
    pv.add_argument(
        "--fail-on",
        choices=("none", "high", "any"),
        default="none",
        help="exit non-zero when confirmed gaps remain (CI gate; default: none)",
    )
    pv.set_defaults(func=cmd_verify)

    pr = sub.add_parser("report", help="write relay-report.json for the dashboard")
    pr.add_argument("directory")
    pr.add_argument("-o", "--output", default="", help="output path (default: <dir>/relay-report.json)")
    pr.set_defaults(func=cmd_report)

    pm = sub.add_parser("mcp", help="run the MCP server")
    pm.set_defaults(func=cmd_mcp)

    args = p.parse_args()
    if args.cmd in ("scan", "verify", "report") and not os.path.isdir(args.directory):
        print(RED(f"not a directory: {args.directory}"), file=sys.stderr)
        return 2
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
