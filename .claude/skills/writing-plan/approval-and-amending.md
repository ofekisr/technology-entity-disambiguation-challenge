# writing-plan — Approval, amending, optional sections

> Detail for [SKILL.md](SKILL.md). On conflict, SKILL.md §Hard rules wins.

## Approval Protocol

**Spec-review gate — the planner runs it before asking for approval.** Read `ex.md` › Deliverables and `V3 › Readiness`, then walk the plan:

- A deliverable bullet no task cites, or no test asserts → fix the plan (add the leaf, add the assertion).
- A task step that cites no V3 section or D-xx → cut it, or find its node.
- A bullet the locked design deliberately does not meet → stop; report to Ofek (he amends the map); never record "not met" in the plan.

The gate is a fix loop, not a report: it ends when the walk finds nothing.

After producing the plan artifact (all sections complete, self-review checklist green, spec-review gate clean):

> ⏸️ WAIT — Review plan. Say 'ok' to hand off to executor, or provide feedback.

**Yolo scope:** `yolo plan` skips approval within this plan-writing session. Still HALT if V3 has a blocking ❗ or a header item is missing.

---

## Amending a plan (adding or re-scoping tasks)

- **Before any verification ran** — normal authoring. Slot the task into the leaf order, prewrite its commit message, re-run the self-review for the new block.
- **After a verification artifact was ticked** — the same edit MUST revoke what it invalidates:
  1. Untick the final verification task's boxes and every Self-review box the new work can falsify (when in doubt, untick).
  2. If the task lands inside an already-closed deliverable (🏁 gate + review done), note that the review record is void; the executor re-opens the group and re-fires the review after the new leaf lands.
  3. Downgrade `**Status:**` from `✅ complete` back to `🟡 in progress`.

---

## Optional final sections

- `## Open items deferred (not blocking this plan)` — table of items explicitly pushed to "doc only" or a later task, each with its owner (a DESIGN.md line, a stub comment, a task id).
- `## Deliverable mapping` — required: one row per `ex.md` deliverable → task range → 🏁 leaf → review task.
