---
id: scrub-private-material-and-machine-paths-from-tracked-files
title: Scrub private material and machine paths from tracked files
type: backlog_item
tags:
- hygiene
- privacy
- public-repo
importance: 5
kind: bug
status: proposed
priority: high
effort: S
rank: 0
---

## Problem

The secrets scan is clean (no credentials in tracked files or history), but the
owner's private work and machine layout leak into a public repo. This ticket
deliberately names **files, not contents**.

- Named subjects of private investigative work and request strategy:
  `kb/backlog/add-blocked-on-optional-field-to-task-schema.md` (lines ~22-36).
  `FEEDBACK.md`'s own rule says such subjects must be placeholders.
- A named private individual in
  `kb/backlog/done/review-flow-web-ui-shelved-superseded-by-google-drive-workflow.md`
  and `kb/backlog/done/full-suite-only-flaky-tests-state-leak-across-test-files.md`.
- Absolute home-directory paths in ~16 tracked files, including `FEEDBACK.md`
  (which also reveals private KB counts), `.claude/skills/pyrite-dev/SKILL.md`,
  `.claude/skills/extension-builder/SKILL.md`, two `kb/notes/` files, and about
  ten `kb/backlog/` files that reference private repositories and the owner's
  local agent-memory directory.
- `.claude/skills/pyrite-dev/release-runbook.md` depends on a gitignored deploy
  script and the owner's sites: mark it maintainer-only.
- `.claude-plugin/plugin.json`: `"author": "markr"`; `plugin.md` still pitches
  "for citizen journalists", which no longer matches the README.

## Fix

Replace subjects and people with placeholders, home paths with `~/…` or
`<repo>`. This cleans the tip only; the content stays in git history. Whether to
rewrite history is the owner's call — decide it explicitly and record the
decision here.

## Acceptance

- [ ] `git grep -n "/Users/"` returns nothing outside fixtures.
- [ ] A grep test (or pre-commit hook) fails on a new absolute home path in a
      tracked file, so this does not recur.

Source: 2026-09-17 project review (three read-only audits: docs/contributor, public-repo, code-health).
