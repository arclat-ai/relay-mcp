# Contributing to Relay

Thanks for taking the time. Relay is small on purpose — one AST engine, six detectors,
one verification pass — so a focused PR is easy to review and easy to merge.

By participating you agree to the [Code of Conduct](CODE_OF_CONDUCT.md).

## Getting set up

```bash
git clone https://github.com/arclat-ai/relay-mcp.git
cd relay-mcp
pip install -e ".[dev]"
pytest
```

Python 3.11+ is required (the engine uses modern `ast` node attributes).

Convenience runners are provided: `./run.sh install` / `.\run.ps1 install`, and
`./run.sh all` to install and register the server with Claude Code. See
[RUNNING.md](RUNNING.md).

## Before you open a PR

```bash
ruff check .        # lint
pytest              # tests
relay verify .      # dogfood the engine on itself
```

CI runs all three on Python 3.11 and 3.12.

## What makes a good contribution

**Bug reports.** The most useful ones include the smallest Python snippet that Relay
gets wrong, plus what it reported and what it should have reported. Open an issue with
the [bug template](.github/ISSUE_TEMPLATE/bug_report.yml).

**False positives.** These matter more than missed detections. Relay's value is that its
output is worth reading; a detector that cries wolf is worse than one that stays quiet.
If you find a pattern that gets flagged but is genuinely fine, that's a bug — file it.

**New detectors.** Very welcome, with one condition: a detector must be able to explain
itself in the verification pass. If you cannot write the one-line reason a finding would
be dismissed, the detector is not ready.

## Adding a detector

1. Create `mcp_server/engine/detectors/<your_detector>.py` with a class that subclasses
   `BaseDetector` and implements `detect(self, timeline: list[Span]) -> list[Finding]`.
   `Span` and `Finding` both live in
   [`mcp_server/engine/base_detector.py`](mcp_server/engine/base_detector.py).
2. Populate the `Finding` fully — `time_lost_ms`, `impact`, `effort`, `code_before`, and
   `code_after` all feed the scorer and the report, and an empty one produces a useless
   finding.
3. Register it in `_DETECTORS` in
   [`mcp_server/engine/engine.py`](mcp_server/engine/engine.py).
4. Teach [`mcp_server/engine/verify.py`](mcp_server/engine/verify.py) how to confirm or
   dismiss your finding type, with a reason string for each outcome.
5. Add a test in `tests/` covering both a true positive and a false positive that your
   verify rule dismisses.

## Style

- No new runtime dependencies. Relay ships with `mcp` and nothing else, and that is a
  feature — it must stay safe to run on a stranger's codebase offline.
- Match the surrounding code: type hints on public functions, `from __future__ import
  annotations` where the module already uses it, comments only where the *why* is not
  obvious from the *what*.
- Keep engine output stable. `schema_version` in `engine.py` exists so the dashboard can
  read older reports — bump it if you change the report shape.

## Commits and PRs

- One logical change per PR. A detector plus a refactor is two PRs.
- Write commit subjects in the imperative mood: "Add prefetch detector", not "added".
- Describe the behaviour change in the PR body, and paste before/after CLI output when
  the change affects what users see.

## Releasing (maintainers)

1. Bump `version` in `pyproject.toml` and add a `CHANGELOG.md` entry.
2. Tag: `git tag v0.4.0 && git push --tags`.
3. The `release` workflow builds and publishes to PyPI via Trusted Publishing.

## Questions

Open a [discussion or issue](https://github.com/arclat-ai/relay-mcp/issues) — a question
that took you an hour to answer is a documentation bug worth filing.
