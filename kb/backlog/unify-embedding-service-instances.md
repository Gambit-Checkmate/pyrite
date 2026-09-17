---
id: unify-embedding-service-instances
type: backlog_item
title: "EmbeddingService is constructed in nine places; /health reports prewarm state for an instance nothing searches with"
kind: improvement
status: proposed
priority: medium
effort: M
created: "2026-09-17"
tags: [embeddings, health, dependency-injection, observability]
---

## Problem

`EmbeddingService` is constructed independently at **nine** call sites. Each
one builds its own instance, so each loads its own `sentence-transformers`
model into memory on first use:

```
pyrite/admin_cli.py:242
pyrite/plugins/context.py:75
pyrite/server/api.py:740          <- the one /health reports on
pyrite/cli/index_commands.py:126, 182, 267
pyrite/services/embedding_worker.py:135
pyrite/services/kb_service.py:91  <- the one search actually uses
pyrite/services/search_service.py:331
```

The observable consequence is a **misleading health endpoint**.
`PYRITE_PREWARM_EMBEDDINGS=true` constructs the instance at `api.py:740` and
stores it on `application.state.pyrite_embedding_svc`; `/health` reports
`embeddings.ready` by reading `.is_warm` off *that* object
(`api.py:804`). But `KBService._get_embedding_svc()` (`kb_service.py:82-94`)
lazily constructs its **own separate** instance for actual search and embed
calls. So `/health` can report ready while the instance serving requests is
cold, or vice versa — the field describes an object no query touches.

## Provenance

Raised by AsyncLegs (Ruslan Terekhov) in PR #5, unprompted, as a disclosed
limitation of his own patch. That PR fixed the real bug — `prewarm()` was
never called at all, so `embeddings.ready` was permanently `false` — and he
flagged that his fix makes the flag *meaningful* without making it
*accurate*:

> A more complete fix would unify these into a single shared instance (e.g.
> via DI), but that's a larger change than this ticket's scope — flagging it
> here in case a maintainer wants to fold it into a follow-up.

His patch still helps beyond the health flag: warming the model on startup
populates the HuggingFace disk cache, so `KBService`'s own first lazy load
hits a warm cache instead of a fresh download+init. The remaining defect is
the duplicated in-memory instance, not the prewarm itself.

## Fix

1. Decide the ownership model. Options, roughly in increasing effort:
   - a module-level singleton keyed by `(db, model_name)`;
   - construct once in `create_app()` and inject into `KBService` /
     `SearchService` / `EmbeddingWorker`;
   - a proper DI seam, consistent with however `QuotaService` /
     `GraphService` / `ExportService` were extracted in the 0.18
     `KBService` decomposition.
   CLI call sites are legitimately separate processes and may stay as they
   are — the unification that matters is *within* a running server.
2. Make `/health`'s `embeddings.ready` read the instance that actually
   serves search.
3. Keep the lazy/optional behavior: `is_available()` and
   `db.vec_available` guards must still short-circuit cleanly when
   `sentence-transformers` is not installed.

## Why it matters beyond tidiness

Two instances means two model loads — roughly double the resident memory for
the embedding model in any server with prewarm enabled, on the surface the
shared-instance pilot peers will be using. And a health field that reports on
the wrong object is worse than no field: it is the kind of silently-wrong
answer this corpus keeps rediscovering (see `FEEDBACK.md`'s 2026-08-28 entry
on a status field that read "clean" when it meant "never checked").

## Acceptance criteria

- One `EmbeddingService` instance per running server process (CLI
  invocations exempt), with a documented owner.
- `/health`'s `embeddings.ready` reflects the instance that serves search and
  embed requests — verifiable by warming, then issuing a `mode=hybrid`
  search, and confirming the flag and the served request agree.
- No regression when `sentence-transformers` is absent: prewarm returns
  `False`, startup completes, search falls back without raising.
