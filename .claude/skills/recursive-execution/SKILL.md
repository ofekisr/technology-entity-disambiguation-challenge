---
name: recursive-execution
description: "Use when executing a plan from writing-plan whose top node has internal sub-nodes (challenge → deliverables → leaves). Default when the plan covers ≥2 ex.md deliverables that must compose."
---

# Recursive Execution (project-local)

Executes a plan **tree** produced by `writing-plan`. Each leaf is one contained task, run by one implementer subagent. Each internal node (a deliverable group) owns a subtree of sibling leaves, and the controller reviews that subtree as a whole before declaring it complete. The project's executor overrides apply at every depth. Why this exists: [rationale.md](rationale.md).

## When to Use / When NOT

- **Use when** the plan has ≥1 **internal node** (a `### D<n>` group), was produced by `writing-plan` with its mandatory header block, and covers ≥2 deliverables that share contracts (`Resolution`, the snapshot schema, the CLI).
- **Use instead** `superpowers:subagent-driven-development` (with the override header inline) when the plan is one deliverable of flat leaves.
- **Halt** if the plan's header block is missing or incomplete, or if depth > 2 without user approval given at session start.

## Input contract

1. **Plan tree**: `challange/docs/plans/<slug>.plan.md`. Internal nodes are its `### D<n>` groups; leaves are its tasks.
2. **`writing-plan` header block** at the top of the plan file. Re-read it; never paraphrase it from memory.
3. **CLAUDE.md invariants** and the override list.
4. **The locked design**: `ex.mmap` › `Design > V3` + D-xx the plan cites, read with a scoped outline script when a leaf's context needs the note text.

If an input is missing, walk the question ladder: plan → V3 / Decisions log → `ex.md` + handoff → CLAUDE.md ([`../_shared/executor-overrides.md`](../_shared/executor-overrides.md)). Never invent task boundaries, commit messages, or contracts.

## Hard rules

Single source of truth: [`../_shared/executor-overrides.md`](../_shared/executor-overrides.md). Root `CLAUDE.md` breaks ties. Gate commands: [`../_shared/greenness-ladder.md`](../_shared/greenness-ladder.md).

1. **The subagent commits its own leaf**, never the controller. It commits only after the greenness gate passes (`guard`; `make test` + extra gate at 🏁 leaves; `sweep` once in the verification task), with the gate's command and output pasted as evidence. It stages explicit paths only and uses the plan's prewritten commit message **verbatim**. If that message is wrong, the subagent halts so the plan can be amended first.
2. **Shape check after each leaf commit, never a diff read.** The controller compares `git show --stat HEAD` with the task's Files list and prewritten message. A missing listed file, or a wrong type or scope, re-opens the leaf. An unlisted file, or drifted wording, is flagged and asked about.
3. **Reviews run per deliverable, never per leaf.** The plan's review task after each 🏁 leaf dispatches one reviewer (`superpowers:requesting-code-review`, `model: 'sonnet'`) for quality plus fidelity to the task text and the D-xx it names. Findings re-open the leaf.
4. **One leaf at a time per parent.** Never dispatch sibling implementers in parallel; they invent duplicate helpers (two normalizers, two slug functions).
5. **Implementer prompt shape.** The first line, verbatim: `Invoke the Skill tool with skill='<name>' before doing anything else.` The prompt must also contain: the full task text; a context paragraph naming sibling order and the shared contract; the commit hard rule; the code conventions and the map rule; the task's self-review checklist; the question ladder; the status report shape `DONE` / `DONE_WITH_CONCERNS` / `NEEDS_CONTEXT` / `BLOCKED`. The subagent never reads the plan file. Template: [leaf-node.md](leaf-node.md).
6. **Approval gates follow the active mode.** Default: pause after every leaf and every subtree. `auto-accept-edits`: pause only at deliverable boundaries. `auto-mode` / `yolo`: never pause. Verification is never skipped in any mode.
7. **Cross-task review at every internal node**, run by the controller with read-only tools after all its children have committed. Four checks, each written as ✅ or ❌ with evidence: shared contracts honored across siblings (`Resolution`, snapshot schema, CLI flags); no duplicate abstractions; shared Pydantic models consistent; no commit relies on a later sibling. The controller also confirms every review task recorded `review: ✅`.
8. **Progress is ticked by the controller.** One TaskCreate entry per node. After each task completes, it ticks the plan file's checkboxes, leaving them **uncommitted** until the final verification leaf. On resume, on-disk ticks are trusted over memory.
9. **A task added after a verification ran invalidates that verification.** Untick it, downgrade `✅ complete` to `🟡 in progress`, re-open a closed subtree. Never grandfather.
10. **After each deliverable boundary, a Hebrew 3-line status** (`done / next / blocked`) to Ofek, per `handoff-deliverables.md`.
11. **Halt and ask the user** when: a Critical review finding that re-opening the leaf cannot fix; the header block is missing; depth > 2; a cited V3 node or D-xx does not exist or contradicts `ex.md`; a failed cross-task contract that needs multiple committed tasks re-shaped; a subagent returns `BLOCKED` on a problem in the plan or the map itself.

## Mandatory header block (controller emits in chat at session open)

1. **Plan path**: the plan file.
2. **Tree shape**: `depth: <N>`, `internal_nodes: <count>`, `leaf_count: <count>`, `siblings_per_internal: <list>`. Halts if `depth > 2` without prior approval.
3. **Override re-statement**, verbatim:
   > CLAUDE.md override: the leaf-executing subagent commits its own leaf after the greenness gate passes (`python -m pytest -q tests/<file>` for a leaf; `make test` + the deliverable's extra gate at 🏁 leaves; `make test && docker build` once, in the final verification task). Reviews (code-quality + fidelity to the task text) are explicit review tasks in this plan — one reviewer, one task immediately after each 🏁 leaf — run by the controller; never per leaf, never only at the end. After every leaf commit the controller checks the commit's shape (`git show --stat` against the task's Files list and prewritten message), never its diff. Approval-gate tier follows the active Claude Code mode (default = per-leaf pause, auto-accept-edits = per-deliverable pause, auto-mode/yolo = no pause). Subagent prompts include `Invoke the Skill tool with skill='<name>' before doing anything else.` Never edit `ex.mmap`.
4. **Verification gates declared**, verbatim list:
   - `superpowers:test-driven-development` per code leaf (subagent first step)
   - `superpowers:verification-before-completion` before every "complete" claim — command + output pasted
   - Quality + fidelity review per **deliverable** — the plan's review task after each 🏁 leaf
   - Shape check per **leaf** — `git show --stat HEAD` vs the task's Files list and message; never the diff
   - Cross-task review per internal node (controller-side, after all children commit)
5. **TaskCreate populated**: one task per plan-tree node, in execution order.

If any of items 1–5 is missing, the controller is malformed. Do not dispatch.

## Where the detail lives

| Read when | File |
|---|---|
| Running a leaf: lifecycle, prompt template, review task, evidence table, commit, shape check, pause text | [leaf-node.md](leaf-node.md) |
| Closing an internal node: lifecycle, cross-task review evidence shapes, subtree declaration | [internal-node.md](internal-node.md) |
| TaskCreate entries, ticking checkboxes, resuming after a crash, mid-run amendments | [progress-tracking.md](progress-tracking.md) |
| Deciding whether to halt and what this skill does not do | [halt-and-stop.md](halt-and-stop.md) |
| Before declaring a leaf or subtree complete | [checklists.md](checklists.md) |
| Why this skill exists, adopted / rejected patterns | [rationale.md](rationale.md) |

Chain: [`../_shared/sdlc-chain-map.md`](../_shared/sdlc-chain-map.md). TDD first-step lines: [`../_shared/tdd-routing.md`](../_shared/tdd-routing.md). Upstream: `writing-plan`. Downstream: `superpowers:requesting-code-review` → `superpowers:finishing-a-development-branch`.
