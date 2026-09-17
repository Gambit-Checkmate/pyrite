---
id: index-health-exit-non-zero-when-unhealthy-and-accept-k-to-scope-to-one-kb
title: 'index health: exit non-zero when unhealthy, and accept -k to scope to one KB'
type: backlog_item
tags:
- cli
- index
- fail-closed
- silent-failure
importance: 5
kind: bug
status: superseded
priority: medium
effort: S
rank: 0
github_issue: 18
---

## Problem

Measured 2026-09-17 on dev (f746722): `pyrite index health` printed `"status": "unhealthy"` (22 missing files, 33 stale entries, 52 malformed-frontmatter) and exited **0**. Any script, CI step, or agent gating on the exit code reads that as healthy. This is the same shape as the fail-closed sweep: a failure converted to success at a boundary.

Second gap: there is no `-k/--kb` option. On a machine with many registered KBs the report is dominated by other KBs, so it cannot serve as a per-project release gate (the pyrite-dev skill's Wave Completion Checklist uses it as exactly that).

Note stdout is clean JSON; warnings go to stderr. Do not regress that.

## Fix

1. Exit 1 when status is unhealthy (consider `--no-fail` for the old behavior).
2. Add `-k/--kb` to scope every check to one KB.
3. Test both: unhealthy fixture -> exit 1; `-k` excludes another KB's problems.

## Superseded 2026-09-17

Tracked as GitHub issue #18 (https://github.com/markramm/pyrite/issues/18) under ADR-0033: bugs live in GitHub, the KB holds the roadmap. This file stays so links resolve; do not update it here.
