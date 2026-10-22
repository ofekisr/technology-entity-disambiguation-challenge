# recursive-execution — Progress tracking and mid-execution amendments

> Detail for [SKILL.md](SKILL.md). On conflict, SKILL.md §Hard rules wins.

## TaskCreate population

At session open, after the mandatory header block:

- One TaskCreate task per plan-tree node (internal `D<n>` + leaf), in execution order.
- Internal-node description includes `(internal — runs cross-task review after children)`.
- Leaf description matches the plan's task title verbatim.
- Mark `in_progress` when its lifecycle starts, `completed` only after:
  - Leaf: commit lands + shape check ✅ + mode-appropriate approval.
  - Internal: all children completed + cross-task review ✅ + review task ✅ + approval.

TaskCreate is mandatory for multi-task execution. Skip only if the user explicitly says not to.

## Plan-file progress ticks (controller-owned)

TaskCreate is session-scoped; the plan file is the durable record. The controller (never the implementer subagent — it doesn't open the plan) ticks each task's checkboxes in `challange/docs/plans/<slug>.plan.md` immediately after marking that task complete.
Ticks ride **uncommitted** and land in the final verification leaf's commit with the status flip (the plan file is in that leaf's `git add` list).
On resume after a crash, trust the on-disk ticks over memory: an unticked box whose commit exists in `git log` means the tick step was missed — tick it and continue.

**Mid-execution amendments branch on when they land.** Added before the owning deliverable closed → slot it into the leaf order and execute normally. Added after a verification ran → the controller unticks the invalidated verification boxes (when in doubt, untick), downgrades `✅ complete` → `🟡 in progress`, and re-opens a closed group: after the new leaf commits, cross-task review and the review task re-fire. Verification re-runs; it is never grandfathered.
