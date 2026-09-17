---
id: choose-a-pypi-distribution-name-and-decide-the-fate-of-pyrite-mcp
title: Choose a PyPI distribution name and decide the fate of pyrite-mcp
type: backlog_item
tags:
- packaging
- release
- go-to-market
importance: 5
kind: improvement
status: proposed
priority: high
effort: M
rank: 0
---

## Problem

The PyPI name `pyrite` is held by a locked account (ADR-0025, amended
2026-09-17); `publish.yml` has never fired and is now manual-only. The
positioning docs depend on "`pip install` in 30 seconds", and today the install
is `pip install git+…@tag`.

Related packaging gaps:
- `pyrite-mcp/` is at 0.20.0, depends on `pyrite>=0.20.0` (uninstallable from
  PyPI). Delete it, or fold it in as a `pyrite-mcp` console-script entry. The
  version-coupling question is raised in ADR-0031.
- The `all` extra omits `postgres`.
- `streamlit` and `requests` are imported but in no extra (see the leftovers
  ticket for `pyrite/ui/`).
- Dependencies have lower bounds only, apart from `mcp<2`.

## Acceptance

- [ ] A distribution name is chosen, registered, and recorded in ADR-0025.
- [ ] `pip install <name>` works from PyPI for a tagged release.
- [ ] `pyrite-mcp/` is either gone or installable.

Source: 2026-09-17 project review (three read-only audits: docs/contributor, public-repo, code-health). Depends on [[single-source-of-truth-for-the-version-asserted-by-a-test]].
