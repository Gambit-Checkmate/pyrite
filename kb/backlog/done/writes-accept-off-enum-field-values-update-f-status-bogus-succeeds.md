---
id: writes-accept-off-enum-field-values-update-f-status-bogus-succeeds
title: 'Writes accept off-enum field values: update -f status=bogus succeeds'
type: backlog_item
tags:
- cli
- validation
- bug
- programmatic-validation
importance: 5
kind: bug
status: superseded
priority: high
effort: M
rank: 0
github_issue: 14
---

## Problem

Probed 2026-09-17 on a software KB:

    pyrite update status-probe -k probe -f status=bogus-value   -> {"updated": true}, exit 0
    pyrite update status-probe -k probe -f priority=9999        -> {"updated": true}, exit 0

`backlog_item` declares its allowed statuses (`index health` reports violations
afterwards under `invalid_statuses`), but nothing checks them at write time. The
pyrite-dev skill tells agents to use the CLI *because* "the CLI validates field
values" — it does not. This is how 75 items were once stranded on
`status: completed`.

Detection-after-the-fact exists in three places (`index health`,
`pyrite schema validate`, QA); prevention exists in none.

## Fix

`KBService.update_entry` / `create_entry` validate declared constraints (enum,
min/max, pattern) for the entry's type before saving, on every surface. Reject
with `VALIDATION_FAILED` and list the allowed values. A `--force` escape hatch for
migrations.

## Acceptance

- [ ] `-f status=<off-enum>` exits non-zero, names the allowed values, and leaves
      the file untouched — CLI, REST and MCP.
- [ ] The skill's claim becomes true, or is removed.

Related: [[schema-constraints-in-mcp-and-rest]] (surfacing constraints to agents),
[[qa-validate-enforce-type-rubrics]], [[core-types-silently-drop-unknown-frontmatter-keys]].

## Superseded 2026-09-17

Tracked as GitHub issue #14 (https://github.com/markramm/pyrite/issues/14) under ADR-0033: bugs live in GitHub, the KB holds the roadmap. This file stays so links resolve; do not update it here.
