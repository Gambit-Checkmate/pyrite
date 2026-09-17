---
id: live-server-integration-tests-for-multi-request-flows-plus-regression-tests-for-the-three-outside-prs
title: Live-server integration tests for multi-request flows, plus regression tests for the three outside PRs
type: backlog_item
tags:
- testing
- server
- programmatic-validation
importance: 5
kind: improvement
status: proposed
priority: high
effort: M
rank: 0
---

## Problem

~4000 tests, yet every bug the outside contributor found came from *deploying
the server and using it as a client*, and none of the three fixes has a
regression test:

- **PR #3** (MCP over SSE): `tests/test_mcp_routes.py` never asserts the emitted
  `event: endpoint` path, so the doubled-path bug could return. Nothing tests
  the install against mcp 2.x.
- **PR #4** (KB created over REST invisible until restart): no test checks that
  `add_kb()` refreshes `_db_kb_cache`. This is the **fourth** occurrence of the
  stale-registry class (closed issues #1, #2, commit 37a37c9) — see
  [[collapse-kb-registry-to-one-source-of-truth]], which this finding should
  raise in priority.
- **PR #5** (embedding prewarm): `tests/test_embedding_prewarm.py` has no
  startup/lifespan assertion, so whether prewarm is wired in is untested.

The common gap: tests that start a real server process and run a multi-request
flow (create a KB over REST, then search it; open an SSE session, then call a
tool). The tests cover what an agent thought to test, not what a user does.
Same family as the MCP dispatch smoke test (done).

## Acceptance

- [ ] A fixture starts `pyrite-server` on a free port against a temp data dir.
- [ ] Flows: create KB over REST then read/search it without restart; MCP SSE
      handshake asserts the endpoint path, then a tool call; startup triggers
      prewarm.
- [ ] Each of the three PR bugs, reintroduced, fails a test.

Source: 2026-09-17 project review (three read-only audits: docs/contributor, public-repo, code-health). Related: [[ci-run-getting-started-tutorial]].
