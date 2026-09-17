---
id: web-the-review-surface-what-did-agents-do-since-i-last-looked-as-the-home-screen
title: 'Web: the review surface - what did agents do since I last looked - as the home screen'
type: backlog_item
tags:
- web
- ui
- review
- roadmap
importance: 5
kind: feature
status: proposed
priority: high
effort: L
rank: 0
---

## Problem

If the pitch is "agents write, you verify", the UI's job is human oversight of
agent work. Today it is built mostly as an authoring tool (WYSIWYG and markdown
editors, slash commands, daily notes, quick switcher, clipper, gallery views) —
a Notion/Obsidian feature list that a solo maintainer will not out-polish and
does not need to, because the files are the source of truth and any editor can
open them. The screens no competitor has — Changes, Merge Queue, QA, Tasks — sit
at the bottom of the sidebar.

ADR-0019 already said it (2026-03): agents produce work faster than humans can
review it, so human review is the constraint. `review_queue` became first-class
in the backend; the UI never caught up.

## What to build

Make "what did agents do since I last looked" the home screen:

- a change feed per agent and per commit, with diffs
- approve and revert
- QA warnings inline
- the task board showing who claimed what, with checkpoints
- provenance on each entry page (commit, author, sources)

Most of the backend exists (claimed tasks, checkpoints, commits, diffs, QA), and
it needs none of ADR-0030's five prerequisites. It works for agents Pyrite did
not launch — Claude Code conductors today, a contributor's agents over MCP.

## Why first

- It is the **shell of the daily-driver local app** (`pyrite-desktop` in
  ADR-0031): agent integration then needs only a "run this" button on a task
  and a live pane streaming the ACP session for display, with checkpoints
  staying the source of truth (ADR-0030 §6). Live run control plugs into the
  same screen later.
- It is a cheap test of whether ADR-0030 Phase 5 is worth its prerequisites.
- A short recording of it is a better product-page hero than a feature grid.

## Sequencing

After the first-visit fixes ([[web-search-results-never-render]],
[[web-kb-context-single-authority]], [[web-sidebar-ia-regroup]],
[[web-light-mode-chrome-repair]], [[web-graph-default-scope-and-guards]]) and
after Playwright is deterministic and blocking
([[playwright-e2e-suite-non-deterministic-failures-likely-shared-state-auth-config-gap]]).
Freeze new authoring features meanwhile.

## Acceptance

- [ ] Home route answers "what changed since I last looked" for a KB with
      agent commits, without opening a terminal.
- [ ] Approve / revert round-trips through the existing review and git services
      (no new storage).
- [ ] Deterministic Playwright coverage for the feed.

Source: 2026-09-17 UI roadmap discussion; full argument in the "Review response"
section of ADR-0031, with ADR-0030 for the run-control half.
