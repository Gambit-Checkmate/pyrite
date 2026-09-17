---
id: first-write-on-a-fresh-install-blocks-over-a-minute-downloading-the-embedding-model
title: First write on a fresh install blocks over a minute downloading the embedding model
type: backlog_item
tags:
- server
- embedding
- onboarding
- bug
importance: 5
kind: bug
status: superseded
priority: high
effort: S
rank: 0
github_issue: 13
---

## Problem

Release validation, 2026-09-17, live `pyrite-server` with an empty home directory:
the first `POST /api/entries` blocked for **more than 60 seconds** (the client
timed out). The entry file had been written; the request was stuck in
`KBService._auto_embed`, which — with no embedding worker configured — calls
`embed_entry` synchronously, and that downloads the sentence-transformers model
(~90 MB) and imports torch inside the HTTP request. The second attempt, with the
model cached, took 3 s, and later writes ~1 s.

Every developer machine has the model cached, so no test sees this. A new user
sees their first write hang with no message. PR #5 (embedding prewarm) addressed
the warm-cache case at startup; it does not cover "model not downloaded yet".

## Fix

- Writes never wait on embedding: without a worker, embed in a background thread
  (or skip, and let `index sync` / the next search catch up).
- Model download is an explicit, visible step: log "downloading embedding model
  (~90 MB), semantic search available when done"; never inside a request.
- `pyrite init` / first server start offers to fetch it.

## Acceptance

- [ ] With an empty HF cache and the network blocked, `POST /api/entries` returns
      in < 2 s and the entry is keyword-searchable (live-server test).
- [ ] The README says the first semantic search downloads a model.

Related: [[live-server-integration-tests-for-multi-request-flows-plus-regression-tests-for-the-three-outside-prs]],
[[unify-embedding-service-instances]].

## Superseded 2026-09-17

Tracked as GitHub issue #13 (https://github.com/markramm/pyrite/issues/13) under ADR-0033: bugs live in GitHub, the KB holds the roadmap. This file stays so links resolve; do not update it here.
