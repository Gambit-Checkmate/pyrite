---
id: plugin-type-resolution-scoping
type: backlog_item
title: "Scope plugin entry-type resolution by KB type: global person→actor remapping is order-dependent and surprises every KB"
kind: improvement
status: proposed
priority: medium
effort: L
created: "2026-07-03"
tags: [plugins, extensions, architecture, audit-2026-07]
links:
- target: extension-registry
  relation: related
  kb: pyrite
---

## Problem

`KBService._resolve_entry_type` (kb_service.py:180-200) iterates ALL
installed plugins' entry types and rewrites requested type names in
EVERY KB, regardless of kb_type: with the cascade extension
installed, `create_entry(type="person")` becomes `actor` in a
generic research KB (this is the mechanism behind the 2026-07-02
docs-audit finding where a fresh tutorial KB immediately failed
`index health` with `undeclared_types` warnings on its own tutorial
entries). Multiple plugins subclass `EventEntry`, so `type="event"`
resolves nondeterministically (dict-iteration order, last-writer-wins
merge at registry.py:199-210, WARN only).

The KB-type scoping machinery EXISTS (`registry.py:508-576`) but is
wired only for hooks and validators — not entry types, DB
tables/columns, or migrations. Related blast-radius items from the
same audit: `PluginContext` hands plugins the live db with
unrestricted DDL (`plugins/context.py:31-36`); the `social` extension
writes via IndexManager/KBRepository directly, bypassing KBService
hooks/validators; `mcp_server.py:35-77` `_UPDATE_FIELDS` leaks
extension vocabulary (`sender`, `funder`, `claim_status`) into core.

Tolerable with 6 first-party extensions; not tolerable the day a
third party writes one — a prerequisite for [[extension-registry]].

## Decision (2026-07-03, Mark): compat-check failures FAIL CLOSED

From the fail-open sweep's site #6 investigation:
`_plugin_matches_kb_type` (registry.py:508-521) already logs its
failure — the open question was the `return True` fail-open. Decided:
**fail closed** — a plugin whose compatibility check errors is
SKIPPED for that KB. Rationale: the check reads static plugin
declarations (errors are structural, not transient), while the blast
radius of a wrongly-applied plugin is global type remapping (the
person→actor tutorial-KB failure). Additionally, per
[[in-band-degradation-signaling]]: the skip must surface in-band
(warnings array / stderr), not log-only — logs are invisible to
CLI/MCP agents.

## Fix

1. ~~Wire the existing KB-type scoping into entry-type resolution:
   a plugin's type remaps apply only in KBs whose kb_type the plugin
   declares. Core type names resolve to core classes everywhere else.~~
   **DONE 2026-09-17 (2452cf2).** See Progress below.
2. Deterministic conflict handling: two plugins claiming the same
   type name in the same scope = hard error at load, not
   last-writer-wins WARN. **STILL OPEN** — `_merge_dict`
   (registry.py:199-210) is unchanged; resolution is now deterministic
   *within* a scope, but a genuine same-scope collision still resolves
   silently instead of failing loudly.
3. Move `_UPDATE_FIELDS` extension vocabulary behind a plugin
   contribution (plugins declare their updatable fields).
   **STILL OPEN** — `sender`, `funder`, `claim_status` still leak into
   core at mcp_server.py:35-77.
4. (Stretch / may split) Narrow PluginContext: schema-scoped DDL,
   and route extension writes through KBService so hooks/validators
   always run. **STILL OPEN.**

## Progress — item 1 done (2026-09-17, commit 2452cf2)

Forced by CI rather than chosen: two journalism-investigation tests
failed on GitHub runners while the full suite passed locally 4013/4013,
twice. Root cause was this ticket's bug, in a sharper form than the
original write-up describes.

**The nondeterminism is per-machine, not per-run.** `_aggregate_dict`
iterates `self._plugins.values()`, ordered by entry-point discovery,
which follows `importlib.metadata`'s site-packages enumeration. Both
cascade's `actor` and social's `user_profile` subclass `PersonEntry`, so
`person` resolved to `actor` on this laptop (cascade discovered first)
and `user_profile` on the Ubuntu runner. Same code, same test, different
host — and the wrong type written silently to disk. No amount of local
re-running surfaces it; it is an install-time coin flip, not a flake.

**What shipped:**

- `Registry._aggregate_dict_for_kb()` + `get_all_entry_types_for_kb()`,
  completing the KB-type-scoped aggregation family. The list and
  dict-of-lists variants and `_plugin_matches_kb_type` already existed
  (the fail-closed decision above is live); only the plain-dict variant
  was missing, which is exactly why entry types were the one unscoped
  consumer.
- `_resolve_entry_type(entry_type, kb_type="")`; both `KBService` call
  sites (`create_entry`, batch create) pass `kb_config.kb_type`.
- Tiebreak is **most-derived-class (longest MRO)**, name as final
  tiebreak. A first draft used `sorted()` — deterministic but arbitrary,
  and it picks `cascade_event` over `timeline_event`, which would have
  silently changed the type of every new entry in the 5,505-entry
  cascade-timeline KB. Caught pre-commit by an explicit regression check
  on that path. MRO depth is principled: `TimelineEventEntry ->
  InvestigationEventEntry -> EventEntry` is strictly more specific than
  a direct `EventEntry` subclass.

**Verified resolution matrix:**

| KB type | requested | resolves to |
|---|---|---|
| cascade-timeline | event | timeline_event (production path intact) |
| cascade-timeline | person | actor |
| known-entities | person | **person** (was `user_profile` in CI) |
| known-entities | event | investigation_event |
| social | person | user_profile |
| generic | person / event | unchanged |

Full suite 4013 passed / 0 failed, identical to baseline; extensions +
plugin/service suites 1088 passed.

**An empty `kb_type` still matches every plugin**, preserving prior
global behavior for callers with no KB in hand. That is a deliberate
compatibility seam, and it is also the remaining hole: any future caller
that forgets to pass `kb_type` silently gets the old order-dependent
behavior back. Worth a follow-up making `kb_type` required once all
callers are known.

## Acceptance criteria

- [x] A generic research KB with all 6 extensions installed:
  `create_entry --type person` yields `person`. Verified directly
  (`generic` and `known-entities` both resolve `person` -> `person`).
- [ ] The getting-started tutorial passes `index health` clean —
  not re-run since the fix; [[ci-run-getting-started-tutorial]] would
  make this continuously verified rather than a one-off check.
- [ ] Load-time hard error test for same-scope type conflicts (item 2).

## Why this stays open

Item 1 was the blast radius; items 2-4 are the rest of the surface the
2026-07-03 audit found. Closing the ticket now would lose them. The
0.25 deferral rationale ("the pilot ships with first-party extensions
only") has also expired for CI purposes: CI installs all six extensions
on every run as of the same day's workflow repair, which is what made
this reproducible at all.
