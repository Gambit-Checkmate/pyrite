---
id: api-authorization-coverage-test
type: backlog_item
title: "No test asserts every /api route is guarded; authorization is applied by convention, not enforced"
kind: bug
status: proposed
priority: high
effort: S
created: "2026-09-17"
tags: [security, api, testing, authorization, ci]
links:
- target: repo-access-is-a-capability-not-a-tier
  relation: related
  kb: pyrite
- target: hosting-security-hardening
  relation: related
  kb: pyrite
---

## Problem

The authorization model exists and is coherent. `create_app()` mounts every
endpoint router behind a baseline:

```python
api_router = APIRouter(
    prefix="/api",
    dependencies=[Depends(verify_api_key), Depends(requires_tier("read"))],
)
```

and 46 `requires_tier` / `requires_kb_tier` guards escalate from there across
nine of the 24 endpoint modules.

**Nothing verifies that the escalation is complete.** There is no test that
enumerates routes and asserts each one carries a guard appropriate to what it
does. A new endpoint added without `requires_kb_tier("write")` inherits only
the read-tier floor and is silently writable by any read-tier caller. The
failure is invisible: the route works, the tests pass, and the gap surfaces
only when someone audits by hand or an untrusted user finds it.

This is the same failure shape this codebase keeps producing, and it is worth
naming as a class:

- `pip install -e ".[dev,postgres]"` exited 0 while installing nothing the
  tests needed (70 collection errors, step reported success)
- `/health`'s `embeddings.ready` reported on an `EmbeddingService` instance
  no query used
- `pytest` collected 0 items from a mistyped path and reported success
- an entry missing `type:` dropped `status:` silently, so guards filtering on
  status read those entries as *clean* rather than *unchecked*

In each case a convention held until it didn't, and nothing failed loudly
when it stopped holding. Authorization is the one where the cost of the
pattern is worst.

## Fix

Add a route-coverage test that runs in CI:

1. Enumerate the API surface via **`app.openapi()["paths"]`**, not
   `app.routes`. FastAPI >= 0.139 wraps included routers in `_IncludedRouter`
   objects without a `.path` attribute, so a naive `.routes` walk breaks —
   `test_collections_plugin.py` and `test_web_clipper.py` were already fixed
   for exactly this (see `ci-make-green-and-load-bearing` item 4).
2. Assert every `/api` path carries an authorization dependency.
3. Assert method implies minimum tier: `POST`/`PUT`/`PATCH`/`DELETE` must
   resolve to at least `write`; a route whose guards top out at the read
   floor is a failure.
4. Maintain an **explicit allowlist** for deliberate exceptions, so adding an
   unguarded route requires editing the allowlist in the same diff — the
   decision becomes reviewable rather than accidental.
5. Extend the same assertion to MCP tools: every tool in `READ_TOOLS`,
   `WRITE_TOOLS`, `ADMIN_TOOLS` should be checked for tier/behavior
   agreement, so REST and MCP cannot drift.

Known exception to encode rather than discover: `GET /kbs/{kb}/daily`
previously performed a write on navigation
(`web-daily-notes-view-side-effect`, fixed). A GET that writes should be a
test failure, not a bug report.

## Open question this surfaces

Two tier systems share three words. MCP has read/write/admin (ADR-0006);
REST has read/write/admin via `requires_tier`. They are structurally
parallel but are separate implementations that can drift, and ADR-0030 §3
proposes per-session MCP tier selection, which makes the relationship
load-bearing rather than incidental. Worth deciding whether they are one
model with two front doors or two models that happen to use the same
vocabulary.

## Acceptance criteria

- A test enumerates every `/api` route and fails on any route lacking an
  authorization dependency.
- A test fails on any write-method route whose guards top out at read tier.
- Deliberate exceptions live in an allowlist, not in the absence of coverage.
- Adding an unguarded endpoint fails CI.
