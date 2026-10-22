# SDLC chain map (shared)

The design-first, executor-aware skill chain for this challenge. Every skill links to its predecessor and successor here so none is an orphan.

```
ex.md (brief)
  → design           (ex.mmap › Design V3 locked + Decisions log D-xx; `hld` / `system-design-process` only if a decision is missing)
  → writing-plan     (one plan file; deliverables = seams; one leaf per commit)
  → recursive-execution            (default when ≥2 deliverables must compose)
    OR superpowers:executing-plans (flat single-deliverable plan)
  → superpowers:verification-before-completion   (`make test` N/N, `docker build`, DESIGN.md ≤ 1 page)
  → superpowers:requesting-code-review           (one pass against ex.md)
  → superpowers:finishing-a-development-branch
```

## Universal entry: `work-kickoff`

`work-kickoff` is the seed-neutral engine every entry point delegates to: **normalize → initial plan → bucket (design/plan/inline via [`bucket-rubric.md`](bucket-rubric.md)) → route → TDD + green gate → doc-sync**.
Its `plan` bucket walks the chain above; its `design` bucket goes back to the mind map (report a gap, Ofek edits the map); its `inline` bucket ships directly.

| Seed kind | Origin |
|---|---|
| `deliverable` | one numbered deliverable of `ex.md` (via `handoff-deliverables.md`) |
| `task` | a human ad-hoc request |
| `bug` | a failing test, a wrong resolution, a Docker break |

## Predecessor / successor table

| Step | Skill / doc | Predecessor | Successor |
|---|---|---|---|
| Design | `ex.mmap` V3 (locked) | `ex.md` | `writing-plan` |
| Plan | `writing-plan` | locked design + `handoff-deliverables.md` | `recursive-execution` \| `superpowers:executing-plans` |
| Execute | `recursive-execution` | `writing-plan` | verification task |
| Execute (flat) | `superpowers:executing-plans` | `writing-plan` | verification task |
| Verify | `superpowers:verification-before-completion` | execute | review |
| Review | `superpowers:requesting-code-review` | verify | `superpowers:finishing-a-development-branch` |

## Design gaps

The map is the design. A skill never edits `ex.mmap`.
A missing or contradictory decision → stop, report the node and the D-xx it conflicts with, ask Ofek one multiple-choice question.

## Invocation

All project skills invoke by **bare name** (`writing-plan`, not `mars-security:writing-plan`).
