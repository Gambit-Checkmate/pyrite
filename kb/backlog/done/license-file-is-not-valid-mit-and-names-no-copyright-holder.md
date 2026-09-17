---
id: license-file-is-not-valid-mit-and-names-no-copyright-holder
title: License file is not valid MIT and names no copyright holder
type: backlog_item
tags:
- hygiene
- legal
- public-repo
importance: 5
kind: bug
status: done
priority: high
effort: XS
rank: 0
---

## Problem

GitHub reports `spdx_id: NOASSERTION` ("Other") for `LICENSE`. A normalized diff
against canonical MIT differs by one omission — the words "to whom the Software
is furnished" — and the copyright line is `Copyright (c) 2025-2026` with no
holder. The defect is inherited: upstream joshylchen/zettelkasten has the same
truncated sentence. History was squashed and the repo is `fork: false`, so
upstream attribution lives only in `UPSTREAM_CHANGES.md`.

## Fix

Replace the body with verbatim MIT text. Two copyright lines: the upstream
author (original Zettelkasten AI Assistant, 2025) and Mark Ramm (2025-2026).

## Acceptance

- [ ] `gh api repos/markramm/pyrite/license --jq .license.spdx_id` returns `MIT`.

Source: 2026-09-17 project review (three read-only audits: docs/contributor, public-repo, code-health).
