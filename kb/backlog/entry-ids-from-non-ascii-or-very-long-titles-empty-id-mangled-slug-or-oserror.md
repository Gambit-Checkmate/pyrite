---
id: entry-ids-from-non-ascii-or-very-long-titles-empty-id-mangled-slug-or-oserror
title: 'Entry ids from non-ASCII or very long titles: empty id, mangled slug, or OSError'
type: backlog_item
tags:
- cli
- bug
- i18n
importance: 5
kind: bug
status: proposed
priority: medium
effort: S
rank: 0
---

## Problem

`generate_entry_id` (`pyrite/schema/validators.py`) is
`re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")`. Probed 2026-09-17 against
a scratch KB:

| Title | Result |
|---|---|
| `日本語のタイトル` | id is empty -> `ERROR: Entry must have an ID`. Nobody can create an entry with a non-Latin title. The message does not say why. |
| `🚀 !!! ???` | same |
| `Café résumé naïve` | `caf-r-sum-na-ve` — letters deleted rather than transliterated |
| a 300-character title | unhandled `OSError: File name too long` traceback |

## Fix

- Transliterate before slugging (NFKD + strip combining marks gets `cafe-resume-naive`
  with the stdlib; non-Latin scripts need a fallback).
- When nothing survives, fall back to a short stable id (e.g. `entry-<8 hex of the
  title hash>`) instead of failing, and say so in the output.
- Cap the slug (~80 chars, cut at a hyphen) so the filename always fits.
- One slug function, used everywhere: see
  [[sw-new-adr-does-not-slugify-punctuation-in-filenames-created-files-end-with-a-blank-line]].

## Acceptance

- [ ] Parametrized test over the table above: every title yields a non-empty id
      matching `^[a-z0-9][a-z0-9-]{0,79}$`, and `pyrite create` exits 0.
- [ ] Existing ids are unchanged for ASCII titles (no mass rename).
