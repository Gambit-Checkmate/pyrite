---
id: docs-counts-generated-or-asserted-from-code
title: Docs counts generated or asserted from code
type: backlog_item
tags:
- documentation
- testing
- ci
- programmatic-validation
links:
- target: mcp-tool-dispatch-smoke-test-every-registered-tool
  relation: related
  kb: pyrite
importance: 5
kind: improvement
status: proposed
priority: medium
effort: S
rank: 0
---

## Problem

Counts in the docs are written once and never revisited. On 2026-09-17:

| Claim | Where | Actual |
|---|---|---|
| "~2500 tests" | `README.md:317` | 3182 in `tests/` + 899 in extensions |
| "22 ADRs" | `README.md:331` | 31 |
| "Ten built-in entry types" | `README.md:157` | 11 (`task` is registered in core) |
| `get_entry_classes()`, `get_cli_app()` | `README.md:163,167` | `get_entry_types()`, `get_cli_commands()` |
| extensions list includes `task`, omits `journalism-investigation` | `README.md:226` | six in `extensions/`, no `task` |
| "24 MCP tools (14 / +6 / +4)", "1500+ tests" | pyrite.wiki | 48 (29 / +11 / +8); ~4080 |
| "583 tests, 11 ADRs" | `kb/positioning/README.md`, `UPSTREAM_CHANGES.md` | as above |
| `__version__ = "0.12.0"` | `pyrite/__init__.py:7` | `pyproject.toml` 0.24.1; `web/package.json` and `pyrite-mcp` 0.20.0 |
| "tracked" flaky-test ticket | `CLAUDE.md` | ticket is in `backlog/done/` |

This has been fixed by hand before ([[fix-readme-for-release]],
[[docs-onboarding-fiction-sweep]] — both done) and drifted again. A manual
sweep is not a fix; the top GitHub referrer for the repo is chatgpt.com, so
these numbers are what gets quoted to prospective users.

## Proposed validation

Two rules, in order of preference:

1. **Don't state what will drift.** Replace exact counts with links or
   commands where the number adds nothing ("see `pyrite sw adrs`").
2. **Where a number or name earns its place, assert it.** A
   `tests/test_docs_facts.py` that derives each fact from code and checks
   the docs agree:
   - MCP tool counts and names per tier ← `tool_schemas.py`
   - plugin protocol method names and count ← `pyrite/plugins/protocol.py`
   - built-in entry types ← the core registry
   - field types ← `FieldSchema.VALID_TYPES`
   - shipped extensions ← `extensions/*/pyproject.toml`
   - ADR count ← `kb/adrs/`
   - every relative link in `README.md`, `CONTRIBUTING.md`, `docs/` resolves
   - one version: `pyrite.__version__`, `pyproject.toml`,
     `web/package.json`, `pyrite-mcp/pyproject.toml` (or derive
     `__version__` from `importlib.metadata` and delete the literal).

   Test counts cannot be asserted cheaply — apply rule 1 to them.

The pyrite.wiki site lives outside this repo; either generate its stats
block from the same source at build time or drop the stat tiles.

## Acceptance

- [ ] Every row in the table above is corrected or removed.
- [ ] `test_docs_facts.py` fails when a tool is added without the README
      tier table changing (or the table is generated and the test checks it
      is current).
- [ ] A single version source; the test fails on disagreement.
- [ ] Runs in CI on PRs, so an outside contributor's change is held to it.

## Notes

Filed from the 2026-09-17 whole-project review; one of five structural
checks (see [[mcp-tool-dispatch-smoke-test-every-registered-tool]] for the
set).
