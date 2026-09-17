---
id: sw-new-adr-does-not-slugify-punctuation-in-filenames-created-files-end-with-a-blank-line
title: sw new-adr does not slugify punctuation in filenames; created files end with a blank line
type: backlog_item
tags:
- cli
- bug
- agent-experience
importance: 5
kind: bug
status: proposed
priority: medium
effort: XS
rank: 0
---

## Problem

`pyrite sw new-adr "Branch flow and test progression: feature branches, green-and-current merges to dev, ..." -k pyrite`
created

    kb/adrs/0032-branch-flow-and-test-progression:-feature-branches,-green-and-current-merges-to-dev,-layered-gates-to-release.md

The title is lower-cased and spaces become hyphens, but `:` and `,` pass
through. A colon is illegal in Windows filenames, so the repo would not check out
there; commas and other punctuation make the path awkward everywhere. `pyrite
create` slugifies titles correctly (its ids contain only `[a-z0-9-]`), so the two
commands disagree.

Related small friction seen the same day: files written by `pyrite create` end
with an extra blank line, so the `end-of-file-fixer` hook fails the first commit
of every CLI-created entry.

## Fix

`sw new-adr` uses the same slug function as `pyrite create`, and caps the length.
The entry writer emits exactly one trailing newline.

## Acceptance

- [ ] A title with `: , / ? "` produces a filename matching `^\d{4}-[a-z0-9-]+\.md$` (test).
- [ ] A freshly created entry passes `pre-commit run end-of-file-fixer` unchanged (test).

Found while writing ADR-0032.

## More instances (CLI probe, 2026-09-17)

- The **MCP tool** has the identical hand-rolled slug:
  `extensions/software-kb/.../plugin.py:1566` (`title.lower().replace(" ", "-")`),
  alongside `cli.py:175`.
- A `/` in the title is worse than a bad filename: `pyrite sw new-adr "Use A/B testing"`
  dies with an unhandled `FileNotFoundError` for `adrs/0001-use-a/b-testing.md`.
- Since 2026-09-17 the repository refuses any id or path that would leave the KB
  (`KBRepository._validate_entry_id` / `_contained`), so these now fail safely — but
  they should not fail at all. Use `generate_entry_id`.
