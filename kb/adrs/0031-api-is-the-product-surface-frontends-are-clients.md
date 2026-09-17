---
id: adr-0031
type: adr
title: "The API Is the Product Surface; Frontends Are Scoped Clients"
adr_number: 31
status: draft
deciders: ["markr"]
date: "2026-09-17"
tags: [architecture, api, frontend, authorization, extensibility, deployment]
links:
- target: adr-0007
  relation: refines
  kb: pyrite
- target: adr-0006
  relation: related
  kb: pyrite
- target: adr-0002
  relation: related
  kb: pyrite
- target: adr-0023
  relation: related
  kb: pyrite
- target: adr-0030
  relation: related
  kb: pyrite
- target: api-authorization-coverage-test
  relation: related
  kb: pyrite
- target: repo-access-is-a-capability-not-a-tier
  relation: related
  kb: pyrite
---

# ADR-0031: The API Is the Product Surface; Frontends Are Scoped Clients

> **DRAFT.** Circulated for iteration, not decision. Open questions at the
> end are genuinely open; several would change the shape of the decision.

## Context

ADR-0007 describes three surfaces — Claude Code plugin, MCP server, Web UI —
sharing one backend. That was right for a single-operator tool. It is now
carrying four distinct products that the word "Web UI" hides:

1. **Operator workspace.** One trusted user, full CRUD, settings, merge
   queue, and (per ADR-0030) local agent run execution. This is what exists.
2. **Public reader.** Untrusted anonymous visitors, read-only, crawlable.
   Partly exists already as the ADR-0023 `/site/` HTML cache, which was built
   precisely because the SvelteKit SPA is invisible to search engines.
3. **Shared instance.** Authenticated but *not fully trusted* users —
   the invited-peer pilot, and later a journalist federation sharing research
   KBs across organizations. Per-user BYOK AI, no run execution, and
   sharing grants that read/write/admin cannot express.
4. **Domain workspace.** A software team using the `software-kb` extension,
   whose vocabulary is ADRs, backlog items, epics, review queues and work
   logs — not entries, tags and collections.

These differ on two independent axes: **who the user is** (trust, scope,
credentials) and **what the domain is** (vocabulary, workflow, affordances).
One application cannot serve all four without conditionals that are neither
reviewable nor enforceable.

### Two facts that shape the decision

**The frontend is already mostly a library.**

```
src/lib/     14,026 LOC   api, components, editor, stores, types, utils
src/routes/   7,929 LOC   19 routes
```

64% of the web app is domain-agnostic machinery. The routes are thin. And
they sort cleanly by audience: `settings`, `merge-queue`, `tasks`, `qa`,
`register`, `login`, `changes`, `daily` are operator-only; `entries`,
`search`, `graph`, `timeline`, `tags`, `collections`, `orient`, `overview`
are reader-plausible. Roughly half the current app has no business existing
on a public instance.

**Plugins extend the backend and stop at the API.** The protocol has 18
extension points — `get_entry_types`, `get_mcp_tools`, `get_validators`,
`get_db_tables`, `get_workflows`, `get_kb_presets`, and so on — and **not
one of them concerns the frontend.** The consequence is visible in
`software-kb`: 10 entry types and 23 `sw_*` MCP tools, a complete domain
model, with no UI of its own. A `backlog_item` and a `timeline_event` render
identically in the generic entry browser. The backend has been
general-purpose since 0.18; the frontend never was.

### The rejected framing, and why

An earlier version of this decision was **deployment modes**: one
application, one API, a mode flag selecting which capabilities are reachable.
Rejected because *a mode flag is runtime state, and runtime state can be
wrong.* If `RunService` exists in the process and configuration decides
whether it is reachable, then a misconfiguration, a bug, or a compromised
settings write turns it on. This is the same objection ADR-0030 §4 makes
about harness gates, and `hosting-security-requirements` REQ-1 states the
principle directly: *"If the capability doesn't exist, it cannot be
compelled."*

A second framing — **two separately-built applications** — was also
insufficient on its own. A build split is a real *product* boundary but not a
*security* boundary: a public app that does not render a fork button does not
prevent anyone from calling `POST /repos/fork` with a write-tier credential.
The endpoint is still there.

The resolution is that these solve different problems and both are needed,
with the API carrying the guarantee.

## Decision (proposed)

**The REST API is the product surface. It carries the complete authorization
model. Frontends are clients that hold credentials, scoped by audience and by
domain. No frontend enforces anything.**

### 1. The API is the only security boundary

Every guarantee about what a principal may do is expressed and enforced in
the API, not in which routes a bundle happens to contain. A frontend omitting
a feature is a product decision; a credential lacking a grant is the
enforcement.

This makes two already-filed tickets prerequisites rather than hygiene:

- [[api-authorization-coverage-test]] — the model exists (router-wide
  `verify_api_key` + `requires_tier("read")` floor, 46 escalating guards) but
  nothing verifies it is complete. Under this ADR, an unguarded endpoint is
  not a latent bug; it is a hole in the only boundary.
- [[repo-access-is-a-capability-not-a-tier]] — read/write/admin is a content
  ladder. Repo, git, and network-egress operations are a different axis,
  currently approximated inconsistently (`repos.py` forks at write tier,
  `git_ops.py` pushes at admin, MCP exposes only `kb_commit`/`kb_push`).

**Neither the public reader nor the shared instance ships before both land.**

### 2. Grants, not modes

Deployment differences are expressed as *which grants a credential carries*,
not as which code is present. A shared instance issues credentials without
the repo/egress capability and without run execution; a local instance issues
one credential with everything.

This keeps the earlier mode-flag objection answered: a grant is data about a
principal, checked on every request, not a global toggle whose failure mode
is silent over-permission.

### 3. Frontends are scoped clients, and there will be more than two

A frontend is characterized by the audience it serves and the domain
vocabulary it speaks. The known instances:

| Client | Audience | Domain | Run execution |
|---|---|---|---|
| Operator workspace | single trusted user | generic KB | yes (ADR-0030) |
| Public reader | anonymous, untrusted | generic KB | no |
| Shared instance | authenticated peers | generic KB + sharing | no |
| Software workspace | trusted colleagues | software-kb vocabulary | operator-dependent |

The first two are near-term; the second two are directions. The point of the
decision is that adding a fifth should require no architectural change.

### 4. `pyrite-core-ui`: the shared library becomes addressable

`web/` is currently `private: true`, has no `exports` map, no `src/lib`
barrel, and a `version` (0.20.0) already drifted from `pyproject.toml`
(0.24.0). It is an application, not a library.

The extraction is a package boundary over the existing 14K LOC: an explicit
public surface, a barrel, peer-dependency handling for Svelte, and a decision
about what is public versus internal.

**Sequencing recommendation:** extract `api` + `types` first as a
framework-neutral client package. A third-party frontend needs typed access
to `/api/*` far more than it needs Svelte components, and that package is
smaller, has no framework coupling, and lets non-Svelte clients participate.
Extract components only when a second real consumer exists.

### 5. Plugins gain a frontend contribution point

Symmetric with the plugin protocol's 18 backend extension points, a plugin
should be able to contribute UI: type-specific renderers, domain routes,
board configurations. `software-kb` is the proving case — if a software team
gets a recognizable project tool rather than a generic entry browser, the
contract works.

**This inherits a lesson from `plugin-type-resolution-scoping`,** where
global, discovery-ordered type remapping resolved `person` differently on
different machines. Any UI contribution point must be **scoped and declared**
— by KB type, per ADR-0029 libraries — never a global registry whose winner
depends on load order.

## Consequences

### Positive

- One enforcement model, testable in CI, rather than a boundary that depends
  on which bundle a user loaded.
- Adding an audience or a domain becomes a client, not a fork.
- The BHAG's four-wave go-to-market (software teams, journalism, PKM) gets a
  frontend story; today every wave would ship the same generic UI.
- The public reader stops being a separate static-rendering pipeline and
  becomes a client like any other — possibly superseding `/site/`, possibly
  not (see open questions).

### Negative

- **Multiple apps multiply the release surface**: build pipelines, e2e suites,
  deploy artifacts. The Playwright suite is currently nondeterministic and
  non-blocking in CI; multiplying it before fixing it would compound a known
  problem.
- **A published `pyrite-core-ui` is a compatibility obligation.** Once a
  second consumer exists, `lib/` changes are breaking changes. The project has
  never cut a GitHub release, has no working PyPI path (the `pyrite` name sits
  on a locked pre-2FA account), and `pyrite-web`'s version has already drifted
  four minors. Taking on npm semver obligations before Python release
  discipline exists is a real risk.
- **A plugin UI contribution point is a new extension surface** with its own
  scoping, conflict, and trust questions — the backend equivalent produced
  ADR-0002, capability declarations, and the type-resolution bug.
- The two prerequisite tickets are now blocking, which lengthens the path to
  a shared instance.

### Neutral

- ADR-0007's three-surface diagram is refined rather than replaced: Surface 3
  becomes a family of clients.
- The operator workspace is unchanged in the near term; it is simply named as
  one client among several.

## Open questions

1. **Does the public reader replace `/site/`, or coexist?** `/site/` exists
   because SPAs are not crawlable. A client-side public reader inherits that
   problem. Keeping both means two public surfaces; replacing means solving
   SSR, which ADR-0023 explicitly tried and abandoned.
2. **Where do BYOK keys live for untrusted users?** ADR-0007 §3 says "keys
   never leave the server," correct when the server is your laptop. On a
   shared instance it puts every user's key inside the legal-compulsion
   surface REQ-3.3 requires you to document. Browser-held keys are a
   different mechanism, not a configuration of that one.
3. **Is `pyrite-core-ui` published, or vendored?** A monorepo workspace
   package with no npm publish avoids the semver obligation while still
   allowing two apps. It also blocks genuine third-party frontends.
4. **How does a plugin UI contribution actually work** in a compiled
   SvelteKit app — build-time registration, dynamic import, or a manifest the
   app reads at runtime? This may be the hardest part of §5 and is unresolved.
5. **Does the shared instance run a different backend** (fewer routers
   mounted, `RunService` never constructed), or the same backend with grants
   doing the work? §2 says grants. §1's "the API is the only boundary" is
   stronger if some capabilities are structurally absent — these are in
   tension and the tension is not resolved here.
6. **Sequencing against 0.25.** Both prerequisite tickets are high priority
   and the shared-instance pilot is the 0.25 epic. Does this ADR block the
   pilot, or does the pilot ship with the operator workspace and a manually
   scoped credential?
