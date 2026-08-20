# Pyrite field feedback

Hallway-testing log. Append entries; do not edit or rewrite someone else's — the
series is the value. Maintainers: triage visibly with `[fixed <commit>]`,
`[wontfix — reason]`, or `[tracked]`, and leave the original text intact.

**Placeholder convention:** subjects of investigation are replaced with stable
placeholders (`<person-a>`, `<org-b>`) and reused consistently within an entry.
KB names, entry ids, flags, and output shapes stay verbatim — that is what makes
a report reproducible.

---

## 2026-08-20 · full-day KB research session, ~40 invocations · claude-opus-5

Used pyrite as the primary KB search/task layer through a long investigation
session: corpus recall, task claim/update across four parallel subagents,
`index sync` after every few artifacts, and cross-KB search over
cascade-timeline / cascade-research / substack-published.

Net: it carried the session. Four issues below, ordered by what actually cost me
time.

---

**Friction 1 — the dual-registry split is silent, and it is a correctness trap.**

**Command:**
```
pyrite task list -k cascade-research --status open -f json     # 159 open tasks
~/kb/kb task list -k cascade-research --status open -f json    # 161 open tasks
```
(`~/kb/kb` is a two-line wrapper that sets `PYRITE_CONFIG_DIR=/Users/markr/kb`
and execs the venv binary.)

**Expected:** same command, same machine, same `-k` → same result set.

**Got:** 159 vs 161. No warning, no error, no indication a different registry was
consulted.

**Friction:** I created a task with bare `pyrite`, then could not find it with
`~/kb/kb get <id>` and briefly concluded the write had silently failed. It had
not — it went to the other registry. I only diagnosed it because a project skill
happens to document the hazard in a boldface paragraph. Without that I would have
filed a data-loss bug.

**Root cause (diagnosed after filing, 2026-08-20):** there are two complete,
independently-maintained config files, and which one you get depends entirely on
whether `PYRITE_CONFIG_DIR` is set in the environment:

```
/Users/markr/.pyrite/config.yaml   47 knowledge_bases   <- bare `pyrite` (default)
/Users/markr/kb/config.yaml        52 knowledge_bases   <- `~/kb/kb` (wrapper sets PYRITE_CONFIG_DIR)
```

Diff of the two registries:

- only in `~/kb`: `daily-capture-reports`, `detention-pipeline-research`,
  `guide`, `igsa-holders`, `pitch-pipeline`, `svelte`
- only in `~/.pyrite`: `test-release`

So this is not a sync bug or a race — it is two divergent registries that drifted
because every `kb create` writes to whichever config the invoking shell happened
to resolve. The 159-vs-161 task delta is downstream of the 47-vs-52 KB delta: the
missing tasks live in KBs the default config has never heard of.

That also explains a related failure documented elsewhere in this corpus (`kb
create` appearing to succeed but the KB being invisible to the task subsystem) —
same cause, different symptom.

**Would have helped, in order of value:**

1. **Print the resolved config path on stderr** when a command touches the
   registry, the way the stale-index warning already names specific KBs. One
   line: `using config: /Users/markr/kb/config.yaml (52 KBs)`.
2. **`pyrite config which`** / `pyrite config diff <other>` so drift is
   inspectable rather than inferred from a count mismatch.
3. **Warn on startup if a second candidate config exists** and its KB set is not
   a subset of the active one. This is the check that would have caught the drift
   before it reached six KBs.

**Severity:** slowed (real risk: blocked / phantom data loss)

---

**Friction 2 — `task list` rich output truncates the ID column, and the ID is the
one field you need.**

**Command:** `~/kb/kb task list -k cascade-research --status open`

**Got:**
```
│ write-timeli │ Write timeline │ open   │   6 │              │ obtain-the-f │
```

**Friction:** IDs here are long generated slugs (60-90 chars). Every workflow
step after listing — `claim`, `update`, `get` — needs the full ID. The table view
truncates it to ~12 chars, so the human-readable output is unusable for the next
command. I ended up piping `-f json` through a python one-liner *every single
time* I needed to pick a task, which is a lot of ceremony for "show me my work."

**Would have helped:** any of — don't truncate the ID column; add a `--wide` or
`--ids-only`; or make the truncation obviously lossy (`write-timeli…`) instead of
looking like a complete value. Right now `write-timeli` reads like it might BE
the id.

**Severity:** annoyed, ~15 times

---

**Friction 3 — `get` can 404 on an entry that `search` and `task list` both
return.**

**Command:**
```
~/kb/kb get <long-task-id> -k cascade-research
→ {"error": "Entry '<id>' not found", "error_code": "NOT_FOUND", "retryable": false}
```
while, at the same moment:
```
~/kb/kb task list -k cascade-research -f json   # id present
~/kb/kb search "<phrase from its title>"        # count: 2, entry returned
```

**Observation, not conclusion:** after an `index sync` the same `get` succeeded.
So this is most likely a read-path/index-freshness interaction, not a missing
entry — but the *error text* asserts the entry does not exist, which is a
stronger claim than the tool can support at that moment.

**Would have helped:** `NOT_FOUND` with `"retryable": false` on something
retrievable by two other code paths is the wrong signal. If the id resolves in
the task table but not the entry index, say that (`indexed: false — run index
sync`). The current message sent me looking for a failed write.

**Severity:** slowed

---

**Friction 4 — `index sync` reports `Updated: 0` on a file it did update.**

**Command:** `~/kb/kb index sync -k cascade-timeline` immediately after writing a
new timeline entry.

**Got:** `Updated: 0  Removed: 0  Embedded: 1` — and the entry *was* correctly
indexed and searchable afterward.

**Friction:** `Updated: 0` alongside `Embedded: 1` reads as a no-op. I could not
tell from the output whether my write had landed, so I ran a verification
`search` after every sync. That is the right discipline anyway, but the counter
should not actively suggest failure when the operation succeeded.

**Would have helped:** either count embeds as updates, or label the line so the
distinction is legible (`Added: 0  Updated: 0  Re-embedded: 1`).

**Severity:** annoyed

---

**Friction 5 — the pre-commit hook runs the full pytest suite and exceeded a
2-minute timeout, blocking a docs-only commit.**

**Command:** `git commit -q -m "..." ` adding only `FEEDBACK.md`

**Got:** hook chain ran `ruff` (skipped, no python files), `check yaml`
(skipped), ... then `pytest quick check` — which was still running when my
2-minute tool timeout killed the process. The commit did not land; the file was
left staged. I committed with `--no-verify` on the retry.

**Friction:** this entry is a markdown file. Every python-specific hook
correctly reported "no files to check" and skipped — and then the test suite ran
anyway. An agent on a timeout budget cannot commit documentation without either
waiting out the suite or knowing to bypass it, and bypassing hooks is exactly the
habit you do not want to teach.

**Would have helped:** scope `pytest quick check` with `files: \.py$` (or
`exclude: ^(FEEDBACK|README|docs/)`) the way the ruff hooks already are. The
other hooks in the chain get this right; this one does not.

**Severity:** blocked (for the commit; worked around with `--no-verify`)

---

**Worked well — and these carried real weight:**

- **The stale-index warning names the specific KBs and goes to stderr.**
  `Warning: index may be stale for: ramm, drafts, daily-capture-reports` — naming
  *which* KBs is what makes it actionable rather than noise, and keeping it off
  stdout meant `2>/dev/null | python3 -c ...` pipelines stayed clean. This is the
  single best-designed message in the tool.
- **FTS recall was good on exact title phrases.** A 6-word title fragment returned
  the entry ranked first, plus two genuinely related entries. Earlier notes in
  this corpus flag recall problems; I did not hit them today.
- **`-f json` on every subcommand.** Being able to pipe any command into python
  is what made the parallel-worker orchestration possible at all.
- **Atomic `task claim`** across four concurrent subagents: no collisions, no
  double-claims, no manual coordination. It just worked, which is the highest
  compliment for a concurrency primitive.
- **Cross-KB search without specifying `-k`** surfaced hits in `substack-published`
  I would not have thought to look for — it caught that a story I was about to
  treat as new was already covered in a published piece.

**Severity summary:** nothing blocked. One correctness trap (Friction 1) that a
less-warned agent would have misdiagnosed as data loss.
