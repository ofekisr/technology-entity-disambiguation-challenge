# writing-plan — Verification task

> Detail for [SKILL.md](SKILL.md). On conflict, SKILL.md §Hard rules wins.

## Verification task (always the final task)

Named `Task N — Verification + companion-doc surface`. **Required skill:** `superpowers:verification-before-completion`.

Steps:

1. `make test` — paste the summary line; report `N/N ✅`.
2. `docker build -t tech-resolver .` — exit 0; then `docker run --rm tech-resolver idx resolve "AWS"` prints a `Resolution`.
3. The four `ex.md` behaviours through the CLI, output pasted: aliases converge; near-collision (`Sentinel` vs `Microsoft Sentinel`) handled per D-xx; hard negative (`Amazon Web Services` ≠ `AWS EKS`); idempotency (two runs, identical output, same `index_version`).
4. `DESIGN.md` one page: `wc -w` ≤ ~600 and every `ex.md` › Deliverable 1 bullet has a heading; every trade-off cites a D-xx; 📊 numbers carry `[CONFIRM]` or a re-measure note.
5. Diagrams exist (`docs/architecture.*`, `docs/resolve-flow.*`) and the flow steps match `ex.md` › Deliverable 3.
6. `README.md` 3 commands match the `Makefile`.
7. Update root `CLAUDE.md` if any convention changed (`claude-md-management:revise-claude-md` as a step).
8. **Re-read `ex.md` › Deliverables and `V3 › Readiness`; map each bullet to file:line.** A bullet the tree does not meet is an open gap with its reason, and the status flip in step 10 is `🟡` not `✅`. A Readiness ❗ is reported to Ofek, not edited.
9. Re-run this plan's Self-review checklist against the shipped tree; tick each box.
10. Flip `**Status:**` to `✅ complete` **only if step 8 found zero unmet bullets**, and confirm every task's step checkboxes are ticked.
11. Final commit (subagent commits its own leaf) — `chore(plan): mark deliverables complete`. Includes the plan file.
12. Hebrew status to Ofek: `done / next / blocked`.

Every plan ships this task. It is not optional.

> **Why step 8 exists.** A plan verifying itself cannot catch a criterion nobody re-read. The brief wins; only a re-read of `ex.md` enforces it.
