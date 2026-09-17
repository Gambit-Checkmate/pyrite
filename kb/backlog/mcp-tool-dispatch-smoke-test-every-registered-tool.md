---
id: mcp-tool-dispatch-smoke-test-every-registered-tool
title: 'MCP tool dispatch smoke test: every registered tool'
type: backlog_item
tags:
- testing
- mcp
- ci
- programmatic-validation
links:
- target: api-authorization-coverage-test
  relation: related
  kb: pyrite
- target: split-mcp-server-module
  relation: related
  kb: pyrite
importance: 5
kind: improvement
status: proposed
priority: high
effort: S
rank: 0
---

## Problem

Nothing calls every registered MCP tool. A handler can be advertised in
`tool_schemas.py`, listed in the README, and crash on every invocation
without any test noticing.

This is not hypothetical. As of 2026-09-17 four read-tier tools —
`task_subtree`, `task_ancestors`, `task_blocked_by`, `task_critical_path` —
raise `AttributeError: 'PyriteMCPServer' object has no attribute '_task_svc'`
on every call (`pyrite/server/mcp_server.py:982, 991, 1000, 1009`; the
property is `task_svc`, cached as `_task_svc_cache`). No file in `tests/`
references any of the four tool names. The suite has ~4000 tests and was
green throughout.

The underlying pattern: tests cover what the author of a change thought to
test. An agent-built codebase grows tool surface faster than anyone
exercises it, so dispatch-level coverage has to be structural rather than
remembered.

## Proposed validation

A parametrized test over the union of `READ_TOOLS`, `WRITE_TOOLS` and
`ADMIN_TOOLS` (plus plugin-contributed tools from the in-tree extensions)
that, for each tool:

1. builds minimal valid arguments from the tool's own JSON schema
   (required fields only; a small per-tool override table where the schema
   alone cannot produce a sensible value, e.g. an existing entry id);
2. dispatches through the same path a real client uses, against a seeded
   temp KB;
3. asserts the result is either a success payload or a *structured* error
   (`error_code` present) — never an unhandled exception.

A second assertion pins completeness: every name in the three tool dicts is
either exercised or listed in an explicit, commented skip table. A new tool
with no entry fails the test.

## Acceptance

- [ ] The test fails on current `dev` for exactly the four tools above
      (RED for the right reason), then passes once `self._task_svc` →
      `self.task_svc` is fixed. Fix the four lines in the same change.
- [ ] Adding a tool to `tool_schemas.py` without a handler, or with a
      handler that raises, fails the test.
- [ ] Runs in the default suite (not marked slow) and in CI.
- [ ] Destructive admin tools (`kb_push`, `kb_registry_remove`, …) run
      against the temp KB / a bare local remote only, or sit in the skip
      table with a reason.

## Notes

Filed from the 2026-09-17 whole-project review as one of five structural
checks that convert a recurring review burden into a gate, in the sense of
ADR-0019's `programmatic_validation`. Siblings:
[[api-authorization-coverage-test]],
[[index-rebuild-from-files-equivalence-test]],
[[docs-counts-generated-or-asserted-from-code]],
[[tests-must-not-inherit-git-env-autouse-fixture]].

Related: [[split-mcp-server-module]] gets safer with this in place;
[[mcp-rest-tool-parity]] can reuse the argument builder.
