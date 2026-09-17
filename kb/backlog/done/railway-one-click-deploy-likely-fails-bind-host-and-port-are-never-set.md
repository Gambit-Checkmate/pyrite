---
id: railway-one-click-deploy-likely-fails-bind-host-and-port-are-never-set
title: 'Railway one-click deploy likely fails: bind host and port are never set'
type: backlog_item
tags:
- deploy
- docs
importance: 5
kind: bug
status: proposed
priority: medium
effort: XS
rank: 0
---

## Problem

Inferred from config, not deployed. `railway.json` sets no `PYRITE_HOST`; the
server default is `127.0.0.1`; neither the Dockerfile nor the server maps
Railway's `$PORT`. Render, Fly and both compose files all set
`PYRITE_HOST=0.0.0.0`. The Railway healthcheck probably never passes, and no
volume is declared despite the README's "persist data at /data".

## Fix

`ENV PYRITE_HOST=0.0.0.0` in the Dockerfile (covers every container target);
honour `$PORT` when set; README notes that Railway needs a manual volume.

## Acceptance

- [ ] A Railway deploy from the README button reaches a passing `/health`, or
      the button is removed until it does.

Source: 2026-09-17 project review (three read-only audits: docs/contributor, public-repo, code-health).
