# writing-plan — Rationale, stop list, cross-references

> Detail for [SKILL.md](SKILL.md). On conflict, SKILL.md §Hard rules wins.

**Why this skill exists:** the executor overrides (subagent commits its own leaf after the gate, mode-driven approval, explicit skill invocation, per-deliverable review) live in CLAUDE.md prose. Borrowed `superpowers:writing-plans` does not carry them, and neither does the mind map. This skill encodes the overrides and the locked D-xx decisions into the one artifact the executor reads.

---

## Hard rules (restated)

- **Subagent implementers commit their own leaf** after the greenness gate. Controller-only commits are deprecated.
- **One task = one leaf = one commit.** A deliverable is a virtual PR, not a commit unit.
- **Env (Makefile / Dockerfile / README) is always the LAST code leaf** — it packages what exists.
- **🏁 marks the last leaf of every deliverable, and a review task follows it.**
- **Cite V3 sections and D-xx by node path** for every decision. "As designed" is not a citation.
- **Never edit `ex.mmap`.** Gaps are reported, not patched.

---

## What this skill does NOT do (stop list)

| Stop doing | Why |
|---|---|
| Inventing decisions the map did not lock | V3 + Decisions log own design; the planner renders them |
| Writing test bodies | The executor invokes `superpowers:test-driven-development` |
| Writing DESIGN.md prose | A docs leaf does it, under `write-markdown` + `elements-of-style` |
| Splitting the challenge across several plan files | One challenge = one plan; deliverables are groups inside it |
| Emitting one task per deliverable | Tasks = leaves. A deliverable expands to multiple leaves |
| Scaffolding `cli.py` or the `Makefile` first | Env and CLI are the last leaves; importing them earlier breaks the leaf-order invariant |
| Collapsing build + resolver + cli into one task | Each is its own leaf in DAG order |
| Budgeting past 4 h | The time box is in `ex.md`; extra scope is "doc only" |

---

## Patterns harvested from `superpowers:writing-plans`

- Bite-sized step granularity, expected output per step, no-placeholder rule, self-review checklist before handoff.

## Patterns NOT harvested

- **TDD baked into the planner** — executor's skill; the planner only declares it.
- **Independent plan-file naming** — replaced by `challange/docs/plans/<slug>.plan.md`.

---

## Cross-References

→ [`../_shared/sdlc-chain-map.md`](../_shared/sdlc-chain-map.md) — where this skill sits
→ [`../_shared/executor-overrides.md`](../_shared/executor-overrides.md) — the override sentence the header encodes
→ [`../_shared/greenness-ladder.md`](../_shared/greenness-ladder.md) — gate commands
→ [`../_shared/tdd-routing.md`](../_shared/tdd-routing.md) — scope → first-step line
→ `challange/ex.mmap` › `Design > V3`, `8. Decisions log`, `7. Test-case bank` — upstream inputs
→ `challange/handoff-deliverables.md` — file layout, locked constraints, done criteria
→ `recursive-execution` / `superpowers:executing-plans` — downstream executors
→ `superpowers:test-driven-development`, `write-markdown`, `excalidraw-draw` — per-leaf required skills
→ `superpowers:verification-before-completion` — the final task
