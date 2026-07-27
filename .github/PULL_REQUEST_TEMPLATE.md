<!--
Thanks for the PR. Keep it to one logical change - a detector plus a refactor is two PRs.
-->

## What this changes

<!-- One or two sentences. Link the issue if there is one: Fixes #123 -->

## Why

<!-- The problem behind the change. -->

## Detector changes

<!-- Delete this section if the PR does not touch the engine. -->

- Detector(s) affected:
- New true positive covered:
- New false positive dismissed (and the reason string):

## Output before / after

<!-- Paste CLI output when the change affects what users see. -->

```
```

## Checklist

- [ ] `pytest` passes
- [ ] `ruff check .` is clean
- [ ] `relay verify .` still runs on this repo
- [ ] Tests added for both the true positive and a false positive, if this touches a detector
- [ ] No new runtime dependencies
- [ ] `CHANGELOG.md` updated under `Unreleased`
- [ ] `schema_version` bumped in `engine.py`, if the report shape changed
