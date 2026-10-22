# work-kickoff — Steps 5–6: green gate, doc-sync

> Detail for [SKILL.md](SKILL.md). On conflict, SKILL.md §Hard rules wins.

### Step 5 — TDD + green gate (MANDATORY, all buckets)
- Route the failing-test tier by scope: [`../_shared/tdd-routing.md`](../_shared/tdd-routing.md).
- Pass the gate: [`../_shared/greenness-ladder.md`](../_shared/greenness-ladder.md) — `inline`/leaf → `guard`; task-done → `verify`; 🏁 deliverable → `verify` + extra gate; final → `sweep`.
- Executor overrides (subagent commits its own leaf, mode-driven approval): [`../_shared/executor-overrides.md`](../_shared/executor-overrides.md).
- **This step is non-negotiable.** No hook enforces it — re-run the gate in the same turn as any status flip.

### Step 5b — Behaviour gate (at the close of the code deliverable)

`make test` proves the suite. Before declaring the code deliverable done, run the four `ex.md` behaviours by hand through the CLI and paste the output:

```bash
make resolve NAME="Amazon Web Services"   # aliases → same canonical as "AWS"
make resolve NAME="Sentinel"              # near-collision → ambiguous or lower confidence, per D-xx
make resolve NAME="AWS EKS"               # hard negative ≠ "Amazon Web Services"
make resolve NAME="AWS EKS" && make resolve NAME="AWS EKS"   # idempotent: identical output
```

### Step 6 — Doc-sync checklist (ADVISORY — emit as TodoWrite, do not skip silently)

**Reference docs read as current state, never as history.** README and DESIGN.md describe what *is*. Strip "previously Y, now Z" (keep Z).

After all work is green, walk this checklist and update whatever drifted:
- [ ] **`DESIGN.md`** — still one page; trade-offs still cite the D-xx that the code implements; 📊 numbers carry `[CONFIRM]` unless re-measured in this session.
- [ ] **`README.md`** — the 3 commands still match the `Makefile`.
- [ ] **root `CLAUDE.md`** — use `claude-md-management:revise-claude-md`.
- [ ] **Plan file** — flip the task's status row to ✅ complete.
- [ ] **`V3 › Readiness`** — report any ❗ to Ofek in the status line; do not edit the map.

Advisory means: not a hard blocker, but emit the checklist so it is visible and consciously skipped, never buried.
