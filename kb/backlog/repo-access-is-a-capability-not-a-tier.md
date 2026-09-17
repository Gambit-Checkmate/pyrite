---
id: repo-access-is-a-capability-not-a-tier
type: backlog_item
title: "Repo/git access is a capability, not a tier: same operations guarded at write in one module and admin in another"
kind: improvement
status: proposed
priority: high
effort: M
created: "2026-09-17"
tags: [security, api, mcp, authorization, architecture, git]
links:
- target: api-authorization-coverage-test
  relation: related
  kb: pyrite
- target: hosting-security-hardening
  relation: related
  kb: pyrite
- target: adr-0006
  relation: related
  kb: pyrite
---

## Problem

read/write/admin is a ladder describing **how much KB content you may
touch**. Repo and git operations are not on that ladder — they are about
**network egress, credential use, and data leaving the box**. Forcing them
onto the content ladder means repo permissions can only be expressed by
over-granting content permissions, or the reverse.

The inconsistency is already in the code. The same conceptual operation
lands at different tiers depending on which module implements it:

| Surface | Operation | Guard |
|---|---|---|
| `repos.py` | subscribe, fork, sync, delete, PR, GitHub repo list | router-wide `requires_tier("write")` |
| `git_ops.py` | publish, commit, push | `requires_tier("admin")` |
| `git_ops.py` | changes | `requires_tier("read")` |
| MCP | `kb_commit`, `kb_push` | `ADMIN_TOOLS` |
| MCP | everything else repo-shaped | **not exposed at all** |

So `POST /repos/fork` and `DELETE /repos/{name}` are write-tier while
`POST /kbs/{kb}/push` is admin, and an MCP agent's repo reach differs from a
REST caller's in both extent and threshold. Nothing about the current model
explains why; it reads as each module's author making a local judgment.

## Why this matters beyond tidiness

**Shared-instance exposure.** `POST /repos/subscribe` and `POST /repos/fork`
cause the server to fetch an attacker-nameable remote — an SSRF-adjacent
surface — and they currently sit behind *write* tier, which a trusted-peer
account on a shared instance would plausibly hold. The web clipper already
has explicit private/loopback/link-local IP blocking for this exact class
(`web-clipper-response-size-cap-and-dns-rebinding-toctou-defense`); the repo
endpoints do not obviously share it. Worth checking as part of this work.

**Legal-compulsion surface.** `hosting-security-requirements` REQ-3.3
requires publishing what a court order against a Tier 3 deployment would
obtain. "Which principals could push KB content to an external remote" is
part of that answer, and it is currently not expressible as a permission.

**ADR-0030 needs it.** §3 proposes per-session MCP tier selection so a
research stage gets read tier and a drafting stage gets write. There is
currently no way to say *"this run may read and write the KB but must never
push to a remote"* — which is exactly the grant an autonomous tick should
have. Per-session tier cannot express it because the axis does not exist.

## Fix

1. Declare repo/git access as a **capability** orthogonal to tier: granted
   per-principal (user, API key, MCP session), defaulting to **off**.
2. Enforce it identically in REST and MCP, from one implementation. Two
   parallel enforcement paths is how `repos.py` and `git_ops.py` drifted in
   the first place.
3. Reconcile the existing guards against the new axis, and record why each
   operation needs what it needs.
4. Audit the fetch-a-remote paths (`subscribe`, `fork`, `sync`) against the
   clipper's SSRF defenses.
5. Probably an ADR rather than a pure implementation ticket — it changes the
   permission model ADR-0006 established, and ADR-0030 depends on the answer.

## Open questions

- Is this one capability or several (`repo:read` / `repo:write` /
  `repo:push-remote`)? Pushing to an external origin is meaningfully
  different from committing locally.
- Does worktree collaboration (ADR-0024) sit on this axis too? The admin
  merge queue is a repo operation performed on another user's behalf.
- Where does the grant live — per-user in the DB, per-API-key, per-library
  in YAML (ADR-0029), or all three?

## Acceptance criteria

- Repo/git access is expressible independently of read/write/admin.
- One enforcement implementation serves both REST and MCP.
- A run can be granted KB write access while being denied remote push.
- Every existing repo/git guard is either reconciled to the new axis or has
  a recorded reason for its current tier.
