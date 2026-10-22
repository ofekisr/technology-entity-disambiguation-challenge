# work-kickoff — Escalation and delegation

> Detail for [SKILL.md](SKILL.md). On conflict, SKILL.md §Hard rules wins.

## Escalation — Q&A then follow-up (the recursion)

When a **design** bucket needs a decision, or any bucket surfaces missing info:
1. Walk the question ladder first ([`../_shared/executor-overrides.md`](../_shared/executor-overrides.md) §Asking the user is the last resort): plan → `ex.mmap` V3 / Decisions log → `ex.md` + handoff → `CLAUDE.md`. Only if all four are silent, ask — one `AskUserQuestion`, what was checked, 2–3 ranked options.
2. Once answered, build a follow-up SEED (`kind: task`, `origin:` = the question + answer) and **re-invoke `work-kickoff`** on it. Ofek records the decision in the map; you never do.
3. A multi-deliverable `plan` bucket delegates to `recursive-execution`, whose leaf subagents may re-invoke `work-kickoff` for nested seeds.

---

## Delegation & the no-auto-load rule

- **Default (controller-inlines):** the controller runs this engine top-level and dispatches leaf implementers with the TDD first-step line, the commit hard-rule, the code conventions and the map rule **inlined** into each prompt. Fragments: [`../_shared/tdd-routing.md`](../_shared/tdd-routing.md) + [`../_shared/executor-overrides.md`](../_shared/executor-overrides.md) §Must-inline.
- **Recursive (subagent re-invokes):** when a dispatched subagent owns a nested seed, its prompt's first step is `Invoke the Skill tool with skill='work-kickoff' before doing anything else.`
- **Model routing:** implementers `sonnet`; read-only lookups `haiku` / `Explore`; DESIGN.md prose may use the parent model.
