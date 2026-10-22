# recursive-execution — Rationale and harvested patterns

> Detail for [SKILL.md](SKILL.md). On conflict, SKILL.md §Hard rules wins.

**Why this skill exists:** `superpowers:subagent-driven-development` runs a flat task list — one controller, one queue, one final review. `superpowers:dispatching-parallel-agents` covers fan-out of independent work but no cross-task review afterward. Neither covers a challenge that ships as five deliverables sharing contracts (`Resolution`, the snapshot, the CLI, the numbers quoted in DESIGN.md): contracts honored across siblings, shared models consistent, no duplicate helpers, no merge-order assumptions. This skill adds that layer.

It also re-encodes the project's executor overrides (subagent commits its own leaf after the gate, per-deliverable review, mode-driven approval gates, explicit skill invocation, never edit the map) so they hold at every depth.

## Patterns harvested

- **From `superpowers:subagent-driven-development`:** fresh subagent per task; controller constructs the prompt (subagent never reads the plan); review at the deliverable as a plan task; model routing (`sonnet` implementers, `haiku`/`Explore` for reads); status handling `DONE` / `DONE_WITH_CONCERNS` / `NEEDS_CONTEXT` / `BLOCKED`.
- **From `superpowers:verification-before-completion`:** evidence + assertion gate before any "complete" claim; rejection of "should", "probably", "seems to"; verification runs in the same turn as the claim.
- **From `superpowers:requesting-code-review`:** SHA-anchored dispatch template (`{DESCRIPTION}`, `{PLAN_OR_REQUIREMENTS}`, `{BASE_SHA}`, `{HEAD_SHA}`).
- **From `superpowers:receiving-code-review`:** reasoned pushback when a reviewer is wrong, citing the D-xx / `ex.md` line relied on.

## Patterns NOT harvested

| Not adopted | Why |
|---|---|
| "continuous execution — do not pause between tasks" | Approval gate follows Claude Code mode |
| `executing-plans`' step-level code blocks assumption | Plans come from `writing-plan` with deliverable-driven structure |
| `dispatching-parallel-agents` parallel implementers | One leaf at a time per parent; parallel implementers invent duplicate normalizers |

## Cross-References

→ [`../_shared/sdlc-chain-map.md`](../_shared/sdlc-chain-map.md) — where this skill sits
→ [`../_shared/executor-overrides.md`](../_shared/executor-overrides.md) — commit / review-tier / approval-gate / skill-loading rules
→ [`../_shared/greenness-ladder.md`](../_shared/greenness-ladder.md) — guard / verify / sweep
→ [`../_shared/tdd-routing.md`](../_shared/tdd-routing.md) — the verbatim first-step line per scope
→ `writing-plan` — upstream: produces the plan tree
→ `challange/ex.mmap` › `Design > V3` — upstream: the contracts cross-task review anchors on
→ `superpowers:subagent-driven-development`, `superpowers:verification-before-completion`, `superpowers:requesting-code-review`, `superpowers:receiving-code-review`, `superpowers:test-driven-development` — pattern sources and per-leaf skills
→ `superpowers:finishing-a-development-branch` — downstream after the root closes
