# `_shared/` — single-source-of-truth fragments for the skill chain

These files hold blocks that `work-kickoff`, `writing-plan` and `recursive-execution` would otherwise restate and drift on.
Each file owns one concern. Skills reference them **by path** instead of restating them.

| File | Owns | Referenced by |
|---|---|---|
| [`bucket-rubric.md`](bucket-rubric.md) | the ONE classification (design / plan / inline) every unit of work uses | `work-kickoff` |
| [`sdlc-chain-map.md`](sdlc-chain-map.md) | brief → locked design → writing-plan → execution → verification → review chain | every skill's Cross-References |
| [`executor-overrides.md`](executor-overrides.md) | who commits, review tier, approval gate by mode, subagent skill loading, question ladder | `writing-plan` header, `recursive-execution` |
| [`greenness-ladder.md`](greenness-ladder.md) | the `guard` / `verify` / `sweep` gate commands (all `make` / `pytest`) + when each runs | `writing-plan`, `recursive-execution` |
| [`tdd-routing.md`](tdd-routing.md) | code / docs / diagram / bug-fix routing + verbatim first-step lines | `writing-plan`, `work-kickoff` |

## Project facts the fragments assume

- Repo: `/Users/ofeki/works/mars-security`. Challenge folder: `challange/`.
- Spec: `challange/ex.md` (the only source of requirements). Design: `challange/ex.mmap` › `Design > V3 (locked)` + `Brainstorm > V2 > 8. Decisions log` (D-xx). Handoff: `challange/handoff-deliverables.md`.
- Stack: Python 3.12, pytest + hypothesis, rapidfuzz, sqlite3, Pydantic at file boundaries. `make setup | test | resolve | eval`, `Dockerfile`.
- Time box: 3–4 h total. Every fragment prefers the smallest step that passes the brief.

## Audience split (load-bearing)

Subagents do **not** auto-load referenced files.

- **Controller-facing** blocks (override table, chain map, gate ladder) live here and are referenced by name — the controller reads them.
- **Subagent-facing** fragments (the verbatim `Invoke the Skill tool with skill='…'` first-step line, the "commit your own leaf" rule, the question ladder) must be **inlined into the dispatched prompt** by the controller.

Each fragment marks whether it is controller-facing or must-be-inlined.

## Invocation namespace

Project skills live in `.claude/skills/` and are invoked by **bare name** — `work-kickoff`, `writing-plan`, `recursive-execution`, `session-retrospective`. No plugin prefix.
