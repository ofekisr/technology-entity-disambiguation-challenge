# work-kickoff — Red flags and cross-references

> Detail for [SKILL.md](SKILL.md). On conflict, SKILL.md §Hard rules wins.

## Red flags — STOP

- "This quick-fix is too small to test" — `inline` still writes the failing test first.
- "I'll flip the plan status to done, tests are probably green" — run the gate in this turn; nothing else checks.
- "V3 doesn't say, I'll pick something sensible" — that is a design bucket; ask Ofek one multiple-choice question.
- "I'll fix the map node while I'm here" — never. `ex.mmap` is Ofek's.
- "This would be better with embeddings / an LLM fallback" — D-01 and D-23 forbid it in the resolve path. Doc only.
- "I'll paste the engine text into the subagent" — no; the subagent re-invokes `work-kickoff`.
- "Docs can wait" — emit the doc-sync TodoWrite and consciously decide.
- "All the plan's tasks passed, so the deliverable is done" — the plan is not the spec. Re-read `ex.md` and the 25-case test bank against the shipped code.
- "Three more hours and it would be production-grade" — the time box is 3–4 h total. Stub it with a comment.

---

## Cross-References

→ [`../_shared/bucket-rubric.md`](../_shared/bucket-rubric.md) — the one classification (design/plan/inline)
→ [`../_shared/sdlc-chain-map.md`](../_shared/sdlc-chain-map.md) — where each route sits in the chain
→ [`../_shared/tdd-routing.md`](../_shared/tdd-routing.md) — failing-test tier per scope
→ [`../_shared/greenness-ladder.md`](../_shared/greenness-ladder.md) — guard / verify / sweep
→ [`../_shared/executor-overrides.md`](../_shared/executor-overrides.md) — commit / review-tier / approval-gate
→ `writing-plan` — the `plan` bucket's route
→ `recursive-execution` / `superpowers:executing-plans` — plan execution
→ `claude-md-management:revise-claude-md` — doc-sync step
→ `challange/handoff-deliverables.md` — the deliverable seeds and locked constraints
