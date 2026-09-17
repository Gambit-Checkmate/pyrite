---
id: db-backup-writes-into-the-current-directory-default-to-the-data-directory
title: db backup writes into the current directory; default to the data directory
type: backlog_item
tags:
- cli
importance: 5
kind: bug
status: superseded
priority: low
effort: XS
rank: 0
github_issue: 21
---

## Problem

`pyrite/cli/db_commands.py:46` writes `pyrite-backup-*.db` into the working
directory. The repo root had accumulated 125 of them (58 MB). They are
gitignored, so nobody noticed.

## Fix

Default the backup path to `<data dir>/backups/`; keep `--output` for an
explicit location. Consider a retention count.

## Acceptance

- [ ] `pyrite db backup` from any cwd leaves the cwd untouched (test).

Source: 2026-09-17 project review (three read-only audits: docs/contributor, public-repo, code-health).

## Superseded 2026-09-17

Tracked as GitHub issue #21 (https://github.com/markramm/pyrite/issues/21) under ADR-0033: bugs live in GitHub, the KB holds the roadmap. This file stays so links resolve; do not update it here.
