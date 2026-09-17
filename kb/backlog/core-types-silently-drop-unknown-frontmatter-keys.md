---
id: core-types-silently-drop-unknown-frontmatter-keys
type: backlog_item
title: "NoteEntry and CollectionEntry silently drop unknown frontmatter keys; only GenericEntry and TaskEntry preserve them"
kind: bug
status: proposed
priority: high
effort: M
created: "2026-09-16"
tags: [models, frontmatter, data-loss, core-types, silent-failure]
links:
- target: issue-pyrite-task-update-strips-non-schema-frontmatter-fields-silently-unparks-monitors
  relation: generalizes
  kb: pyrite
- target: bug-pyrite-silent-index-failure
  relation: related
  kb: pyrite
---

## Problem

A frontmatter key a core entry type does not declare as a schema field is
**silently discarded** on load. No error, no warning in structured output, no
trace in the written file afterward. Only `GenericEntry` (`models/generic.py`,
`_KNOWN_KEYS`) and now `TaskEntry` (`models/task.py`, `_TASK_KNOWN_KEYS`)
collect unrecognized keys into `metadata` and promote them back on save.

Measured 2026-09-16 against the current `dev` tree:

```
NoteEntry        metadata={}  survives_roundtrip=False
CollectionEntry  metadata={}  survives_roundtrip=False
```

Both were handed a `parked_awaiting:` and a `some_custom:` key; both returned
an empty `metadata` and emitted neither key back out. `models/` has five
files defining `from_frontmatter` (`generic.py`, `task.py`, `collection.py`,
`core_types.py`, `base.py`) and exactly two carry a known-keys guard.

## Why this is the same bug twice, not two bugs

This is the general form of two incidents already on the record:

1. **`parked_awaiting:` silently unparked** — the conductor/dispatch
   convention for marking a task legitimately waiting rather than stalled is
   not a `TaskEntry` schema field. `task claim` / `task update -s` round-trip
   the file (load -> mutate -> save) and dropped it, so parked monitors
   silently became indistinguishable from stalled work. Fixed for `TaskEntry`
   only; see
   [[issue-pyrite-task-update-strips-non-schema-frontmatter-fields-silently-unparks-monitors]].

2. **The phantom 258-entry integrity crisis** (`FEEDBACK.md`, 2026-08-28) —
   an entry missing `type:` falls back to `NoteEntry`, which does not inherit
   `Statusable`, so `status` has structurally nowhere to land and is dropped
   before the SQL write. The warning line prints
   `available_keys=[... 'status' ...]`, proving the field is present at
   warning time and lost downstream. That entry's **top recommendation** is
   this ticket:

   > Make `status` (and any field a core/plugin type declares) survive the
   > `note` fallback. The cleanest fix: `NoteEntry` (or the generic fallback
   > path) should preserve unrecognized-but-present frontmatter fields rather
   > than silently dropping anything the target dataclass doesn't declare.

   Live exposure recorded at the time: **28 entries** across `drafts` (22),
   `cascade-research` (5) and `book-drafts` (1) indexing with `status` NULL.

The failure mode is what makes this high priority rather than medium: a
dropped field is indistinguishable from a field that was never set. Every
downstream guard that filters on it reports the affected entries as *clean*
rather than *unchecked*.

## Fix

1. Lift the known-keys pattern out of the per-type copies. `GenericEntry` and
   `TaskEntry` now carry near-identical logic; a third copy in `NoteEntry`
   would confirm it belongs in a shared mixin or a `base.Entry` helper
   (`collect_unknown_keys(meta, known) -> dict`) rather than in each type.
2. Apply it to `NoteEntry` and `CollectionEntry`, and audit
   `core_types.py`'s remaining types for the same gap.
3. Decide the on-disk shape once, centrally: `TaskEntry` promotes unknown
   keys to **top level** (so `^parked_awaiting:` greps work) and pops the
   nested `metadata:` block. Whatever the answer, it should be one decision
   documented in one place, not re-litigated per type.
4. Add a test that parametrizes over **every** registered core entry type and
   asserts an unknown key survives a load -> mutate -> save round trip. This
   is the regression lock that stops the pattern being forgotten on the next
   type added — the fix above is worth little without it.

## Known adjacent defect (found while reviewing the TaskEntry fix)

`_TASK_KNOWN_KEYS` is missing five real `TaskEntry` dataclass fields:
`assigned_at`, `date`, `start_date`, `end_date`, `kb_name`. They are
therefore classified as "unknown" and swept into `metadata`. `assigned_at` is
the one that bites: it is set by `claim_task` but not emitted by
`to_frontmatter`, so today it round-trips *only* by accident, laundered
through `metadata` as an unknown key. `kb_name` is runtime context and should
arguably never reach frontmatter at all. Fix alongside, and decide explicitly
whether `assigned_at` should be persisted.

## Acceptance criteria

- `NoteEntry` and `CollectionEntry` preserve unknown top-level frontmatter
  keys across a load -> mutate -> save round trip.
- The known-keys logic exists in **one** place; `GenericEntry` and
  `TaskEntry` consume it rather than carrying private copies.
- A parametrized test covers every core entry type, so a newly added type
  fails the suite unless it participates.
- `_TASK_KNOWN_KEYS` matches `TaskEntry`'s dataclass fields exactly (no
  schema field classified as unknown), with `assigned_at`'s persistence
  decided deliberately.
- The `status`-specific case from the 2026-08-28 FEEDBACK entry is covered:
  an entry missing `type:` retains `status:` in its frontmatter after a
  round trip, whatever type it falls back to.
