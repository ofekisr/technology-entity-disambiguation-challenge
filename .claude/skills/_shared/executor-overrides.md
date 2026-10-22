# Executor overrides (shared)

These override the defaults in `superpowers:subagent-driven-development`.
Skills reference this file instead of restating the table. Root `CLAUDE.md` is the tie-breaker on conflict.

## The override table (controller-facing)

| Override | Default (overridden) | Project behavior |
|---|---|---|
| **Who commits** | Implementer subagent commits per task | **The leaf-executing subagent commits its own leaf** after the greenness gate passes. Controller-side commits are deprecated — subagents finished, the controller forgot, work sat uncommitted. |
| **When commits land** | After implementer self-review | After the **greenness gate** — [`greenness-ladder.md`](greenness-ladder.md). Leaf = `guard`; 🏁 deliverable leaf = `verify` + the deliverable's extra gate; `sweep` once, in the final verification task. |
| **Review tier** | Final review after all tasks | Reviews are **explicit review tasks in the plan**, one immediately after each 🏁 leaf — one reviewer per deliverable, quality + fidelity to the task text. Never per leaf, never only at the end. Spec compliance is the final verification task's `ex.md` re-read. |
| **Per-leaf shape check** | none | After every leaf commit the controller compares `git show --stat HEAD` with the task's Files list and prewritten message. Listed-but-untouched = re-open; unlisted = flag; type/scope mismatch = re-open. Never reads the diff. |
| **Approval gates** | Continuous; no human in loop | **Driven by Claude Code mode** — default: pause after every leaf; `auto-accept-edits`: pause only at a deliverable boundary; `auto-mode`/`yolo`: no pauses. |
| **Subagent skill loading** | Skills assumed loaded | Subagent prompts MUST inline the first-step line (below); skills do NOT auto-load in subagents. |
| **Task tracking** | TodoWrite optional | **TaskCreate at session open is mandatory** for multi-task execution. |
| **Plan-file progress ticks** | Plan untouched until the end | **The controller ticks each task's checkboxes in the plan file right after that leaf completes.** Ticks ride uncommitted; the final verification leaf commits them with the status flip. A task added after a verification ran unticks every box it invalidates and downgrades `✅ complete` → `🟡 in progress`. |
| **Status line after each deliverable** | none | Per `handoff-deliverables.md`: stop after each deliverable with 3 lines — `done / next / blocked` — in Hebrew to Ofek. |

## Must-inline fragments (subagent-facing — paste into the dispatched prompt)

- **First step:** `Invoke the Skill tool with skill='<name>' before doing anything else.` (`<name>` per [`tdd-routing.md`](tdd-routing.md).)
- **Commit hard-rule:** `Commit your own leaf after the greenness gate passes, using the plan's prewritten commit message verbatim. git add explicit paths only (no git add . / -A). Do NOT commit before the gate is green. If the commit message looks wrong, stop and report back — do not paraphrase.`
- **Code conventions:** the block in [`tdd-routing.md`](tdd-routing.md) §Code conventions.
- **Map rule:** `Never edit challange/ex.mmap. If the design is wrong, return BLOCKED with the node path and the D-xx it conflicts with.`

## Asking the user is the last resort (controller-facing; fragment below must be inlined)

Before asking, walk the sources in this order and stop at the first that answers:

1. **The plan** — the task block, the header (`Spec`, `Source design`, `Architecture`), the File Map, `Open items deferred`.
2. **The locked design** — `ex.mmap` › `Design > V3 (locked)` sections 1–13, then `Brainstorm > V2 > 8. Decisions log` (D-xx `Why:` / `Evidence:`).
3. **The brief and the handoff** — `ex.md`, then `handoff-deliverables.md` §Locked constraints.
4. **`CLAUDE.md`** — project root, then `~/.claude/CLAUDE.md`.

Only when all four are silent, ask — one question, in this shape:

- Line 1: the decision, one plain sentence.
- Line 2: `Checked: plan, V3 §x, D-yy, ex.md §z, CLAUDE.md — none decide it.`
- Then 2–3 options, recommended first, one line each with its trade-off. Use `AskUserQuestion`.

Never bundle questions. Never ask what a grep or a map outline would answer.

**Must-inline fragment (subagent-facing):** `Before returning NEEDS_CONTEXT, look for the answer in this order: the task text you were given → ex.mmap Design V3 / Decisions log → ex.md and handoff-deliverables.md → CLAUDE.md. Return NEEDS_CONTEXT only with the list of what you checked and the one question left.`

## Approval-gate matrix (controller-facing)

| Mode | Leaf-level pause | Deliverable-boundary pause | Plan-root pause |
|---|---|---|---|
| default | WAIT for `ok` | WAIT for `ok` | WAIT for `ok` |
| `auto-accept-edits` | pass through | WAIT for `ok` | WAIT for `ok` |
| `auto-mode` / `yolo` | pass through | pass through | pass through |

## Subagent-dispatch rules (controller-facing)

- **Model routing:** implementer/synthesis subagents `model: 'sonnet'`. Opus only for the DESIGN.md prose or a cross-file reasoning leaf. Read-only dispatches (find, grep, read, report) use `model: 'haiku'` or the `Explore` agent.
- **Comment discipline:** inline "no docstrings explaining what a function does; the name carries it. The only comments allowed are the production-stub notes `ex.md` asks for."
- **Dispatcher output contract:** a prescriptive `## Output` file list makes the subagent skip companion updates (README, Makefile target). List them explicitly or write a thin prompt and trust the skill — never mix.
- **Reading the map:** subagents read `ex.mmap` with a Python + json outline script scoped to one node path. Never dump the whole map (~1,400 nodes).
- **Task numbering:** `Dn.m` = deliverable n, leaf m. Grouping, not build order — read `Depends on:` before sequencing.
