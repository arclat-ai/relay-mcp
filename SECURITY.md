# Security Policy

## Supported versions

Relay is pre-1.0. Security fixes land on the latest released version on PyPI; there are
no backports to older minor versions.

| Version | Supported |
|---------|-----------|
| 0.3.x   | ✅        |
| < 0.3   | ❌        |

## Reporting a vulnerability

**Please do not open a public issue for a security problem.**

Report it privately through
[GitHub Security Advisories](https://github.com/arclat-ai/relay-mcp/security/advisories/new),
or by email to **abdur@lythe.ai**.

Please include:

- what the issue is and roughly how bad you think it is,
- the steps or a minimal repository that reproduces it,
- the Relay version (`pip show relay-mcp`) and your Python version.

You can expect an acknowledgement within 3 business days and an assessment within 7. If
the report is confirmed, we will agree a disclosure timeline with you and credit you in
the advisory unless you prefer otherwise.

## Threat model

Relay is a local, offline tool. It is worth being explicit about what that means:

- **Relay makes no network requests.** It does not phone home, has no telemetry, and
  sends nothing to any server. Report any observed outbound connection as a
  vulnerability.
- **Relay reads source code you point it at**, parsing it with Python's `ast` module. It
  does **not** import, execute, or evaluate the code being audited.
- **Relay writes to two places**: `relay-report.json` in the audited directory, and the
  audit cache at `~/.relay/last-audit.json`. `apply_fix` also writes to a source file,
  but only when explicitly called with `dry_run=false`.
- **As an MCP server, Relay is driven by an LLM agent.** `apply_fix` modifies files on
  disk. It defaults to a dry run for that reason. Review diffs before writing, and run
  agents against version-controlled checkouts.

Anything that breaks one of the guarantees above - a path traversal that writes outside
the target directory, code execution during parsing, an unexpected network call - is in
scope and we want to hear about it.
