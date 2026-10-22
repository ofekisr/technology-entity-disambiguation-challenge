# recursive-execution — Halt rules and stop list

> Detail for [SKILL.md](SKILL.md). On conflict, SKILL.md §Hard rules wins.

## Halt rules

The controller halts and asks the user when:

1. A review task surfaces a **Critical** issue (per `superpowers:receiving-code-review` severity tiers) that re-opening the leaf cannot fix.
2. The plan lacks the mandatory header block from `writing-plan`.
3. Tree depth > 2 without prior user approval.
4. A V3 node or D-xx the plan cites does not exist in `ex.mmap`, or contradicts `ex.md` — the subagent has nothing to implement against. Report the node path; Ofek edits the map.
5. Cross-task review surfaces a failed contract that would require re-shaping multiple committed tasks (e.g. a `Resolution` field mismatch between resolver and CLI). Surface the finding; let the user choose revert, amend-the-plan, or accept-with-followup.
6. A subagent returns `BLOCKED` and the blocker is in the plan or the map itself — re-dispatch will not fix it.
7. The time box is exhausted (4 h) with deliverables open — stop, report what is green, propose what moves to "doc only".

Halt = stop dispatching; surface the finding with evidence; wait for the user. Status to Ofek in Hebrew.

## Stop list (this skill does NOT do these)

| Stop | Owner |
|---|---|
| Author plans | `writing-plan` |
| Decide design | `ex.mmap` V3 + Decisions log (Ofek) |
| Edit `ex.mmap` | Ofek, never an agent |
| Write tests | Subagent implementer via `superpowers:test-driven-development` |
| Commit a leaf from the controller | Project override — the subagent commits its own leaf |
| Continue past a failed review task | Re-open leaf; re-dispatch; re-verify; re-review |
| Skip approval gates because "the task was small" | Mode dictates gating |
| Add an LLM / embedding fallback because the resolver misses a case | D-01 / D-23 forbid it; fix the dictionary or report |
