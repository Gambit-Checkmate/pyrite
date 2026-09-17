---
id: ci-parity-lint-extensions-and-enforce-the-fix-needs-a-test-rule
title: 'CI parity: lint extensions and enforce the fix-needs-a-test rule'
type: backlog_item
tags:
- ci
- contributor-experience
- programmatic-validation
importance: 5
kind: improvement
status: proposed
priority: medium
effort: S
rank: 0
---

## Problem

After [[fast-commit-hooks-full-suite-at-pre-push-ci-is-the-gate]], CI runs the
import-cycle and KB schema checks. Still missing:

- **Ruff covers `pyrite/ tests/` only.** `extensions/` had 60 lint errors (29
  I001, 19 F401, 7 F841) and 55 files that would be reformatted. The commit hook
  *does* lint extension files, so the first person to touch one inherits its
  whole lint debt in an unrelated commit (hit on 2026-09-17 while committing the
  MCP dispatch fixes — two journalism-investigation files had to be reformatted
  to get a three-line fix in).
- **`check_fix_commit_has_tests`** runs only as a local commit-msg hook. CI does
  not check PR commits, and all three outside PRs were fixes without tests.
- mypy is `continue-on-error` with 582 errors in 69 files — tracked by
  [[enforce-mypy-strict]] and the storage burn-down ticket; listed here only so
  the CI picture is in one place. Playwright likewise (its own ticket).

## Fix

One mechanical commit: `ruff check --fix` + `ruff format` over `extensions/`,
then add `extensions/` to the CI ruff step. Add a CI step that runs
`check_fix_commit_has_tests.py` over the PR's commit range.

## Acceptance

- [ ] `ruff check pyrite/ tests/ extensions/` is clean and enforced in CI.
- [ ] A `fix:` commit without a tests/ change fails CI on a PR.
- [ ] `tests/test_dev_process_config.py` pins both.

Source: 2026-09-17 project review (three read-only audits: docs/contributor, public-repo, code-health).
