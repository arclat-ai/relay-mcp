# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Contribution guide, code of conduct, security policy, and issue/PR templates.
- Lint job (`ruff`) in CI and a Trusted Publishing release workflow for PyPI.
- Dependabot for GitHub Actions and pip.

### Changed
- Rewrote the README around the local, no-key model, with the Relay lockup and CLI
  screenshot.
- Dropped the stale `.env` / `.env.example` and `mcp_server/requirements.txt`;
  dependencies live in `pyproject.toml` only.

## [0.3.0]

### Added
- `relay verify --fail-on {none,high,any}` as a CI gate — exits non-zero when a confirmed
  gap remains.
- MIT license, GitHub Actions CI on Python 3.11 and 3.12, and a `dev` extra.

### Changed
- Removed API-key gating and remote usage sync. Relay is now fully local: no account, no
  backend, no network calls.

## [0.2.0]

### Added
- Semantic verification pass — every structural finding is re-read in context and either
  confirmed or dismissed with a one-line reason.
- The `relay` CLI (`scan` / `verify` / `report` / `mcp`), sharing the engine that backs
  the MCP tools.
- Cost-aware dismissal for parallelization findings.

### Fixed
- Detector false positives across the audit engine.

## [0.1.0]

### Added
- Initial MCP server with the AST-based audit engine and six detectors: `SyncOutput`,
  `SequentialTools`, `CacheMiss`, `BlockingIO`, `ColdStart`, and `Prefetch`.
- MCP tools `audit_codebase`, `get_findings`, `verify_audit`, and `apply_fix`.
- `relay-report.json` output for the Relay dashboard.

[Unreleased]: https://github.com/arclat-ai/relay-mcp/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/arclat-ai/relay-mcp/releases/tag/v0.3.0
[0.2.0]: https://github.com/arclat-ai/relay-mcp/releases/tag/v0.2.0
[0.1.0]: https://github.com/arclat-ai/relay-mcp/releases/tag/v0.1.0
