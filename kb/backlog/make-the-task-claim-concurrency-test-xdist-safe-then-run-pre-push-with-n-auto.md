---
id: make-the-task-claim-concurrency-test-xdist-safe-then-run-pre-push-with-n-auto
title: Make the task-claim concurrency test xdist-safe, then run pre-push with -n auto
type: backlog_item
tags:
- testing
- ci
- dev-process
links:
- target: fast-commit-hooks-full-suite-at-pre-push-ci-is-the-gate
  relation: related_to
  kb: pyrite
importance: 5
kind: improvement
status: proposed
priority: medium
effort: S
rank: 0
---

## Problem

`tests/test_task_claim_concurrency.py::TestClaimTaskConcurrency::test_n_processes_race_claim_exactly_one_wins`
fails under `pytest -n auto` and passes standalone (13s). It spawns N worker
processes and waits with fixed timeouts (`p.join(timeout=30)`,
`result_queue.get(timeout=5)`); when xdist already saturates every core the
workers starve past the timeout.

Measured 2026-09-17: `pytest tests/ extensions/ -n auto` = 2m19s, 4063 passed,
this 1 failed. Serial `tests/` alone = 7m41s. It is the only thing between the
pre-push hook and a ~3x faster gate.

## Proposed fix

Either run the file outside the xdist pool (`@pytest.mark.xdist_group` plus
`--dist loadgroup`, or a `serial` marker run as a second invocation), or make
the timeouts scale with load. Then switch `pytest-full` in
`.pre-commit-config.yaml` (and optionally CI) to `-n auto`, and update
`tests/test_dev_process_config.py` if the entry shape is pinned.

## Acceptance

- [ ] `pytest tests/ extensions/ -n auto` is green 5 runs in a row locally.
- [ ] Pre-push hook uses `-n auto`; CLAUDE.md hook table updated.
