---
name: work-kickoff
description: "Use as the entry point for ANY unit of work in this repo — an ex.md deliverable, an ad-hoc task, or a bug — at the moment you have a seed and need to turn it into shipped, green, doc-synced change. The universal kickoff engine."
---

# Work Kickoff (project-local) — the universal kickoff engine

One pipeline for every seed: **normalize → initial plan → bucket → route → TDD + green gate → doc-sync**.
The bucket rubric, route table, gate and doc-sync checklist live **only here** so nothing drifts.

## When to Use

- You have a **seed** and need it shipped: one of the five `ex.md` deliverables, an ad-hoc task, or a bug.
- A bucket expanded into a nested seed (a design question that spawned new work) — re-invoke this skill on the nested seed.

## When NOT to Use

- You are already mid-execution inside a `writing-plan` plan → that's `recursive-execution` / `superpowers:executing-plans`, not a fresh kickoff.
- The change is a one-line edit with no test surface and no doc impact → just do it (still write the test if any behavior changes).

## Input contract

- A SEED: `{ kind: deliverable | task | bug, origin: <path or ref>, items: [{ title, context, artifacts }] }`.
- A human ad-hoc request becomes one `task` item. A deliverable's origin is `ex.md › Deliverable N` + the matching row in `handoff-deliverables.md`.

## Hard rules

1. **Pipeline order is fixed:** normalize → initial plan → bucket → route → TDD + green gate → doc-sync. Initial plan only enumerates work units; no design or code yet.
2. **Bucket every unit** as design / plan / inline per `../_shared/bucket-rubric.md`. Present the bucketed table and pause for confirmation in non-auto modes.
3. **Route per bucket.** design → report the gap and ask Ofek one multiple-choice question (never edit `ex.mmap`); plan → `writing-plan`, then `recursive-execution` (multi-deliverable) or `superpowers:executing-plans` (flat); inline → do it directly. A design answer re-buckets into plan/inline.
4. **No locked decision, no `writing-plan`.** Every plan step cites a V3 section or a D-xx. A step that cannot is a design bucket.
5. **TDD + green gate is mandatory for every bucket, and no hook enforces it.** Failing-test tier per `../_shared/tdd-routing.md`. Gate per `../_shared/greenness-ladder.md`: inline/leaf → `guard`; task-done → `verify`; 🏁 deliverable → `verify` + extra gate; final → `sweep`. Re-run the gate in the same turn as any status flip.
6. **Time box is a constraint, not a wish.** 3–4 h total across all deliverables. Anything beyond the brief's tests goes to "doc only" (a stub comment or a DESIGN.md line), never to code.
7. **Doc-sync is advisory but never silent.** Emit the checklist as a `TodoWrite` block: `DESIGN.md`, `README.md`, root `CLAUDE.md`, the plan file status row, `V3 › Readiness` (report ❗ to Ofek, do not edit the map).
8. **Escalation ladder before asking the user:** plan → `ex.mmap` V3 / Decisions log → `ex.md` + handoff → `CLAUDE.md`. Only if all four are silent, ask one question with what was checked and 2–3 ranked options.
9. **Subagents don't auto-load skills.** The controller inlines the TDD first-step line, the commit rule and the map rule into leaf prompts. A subagent owning a nested seed gets this first step: `Invoke the Skill tool with skill='work-kickoff' before doing anything else.`
10. **The plan is not the spec.** Re-read `ex.md` › Deliverables and the test bank against the shipped code before any ✅.
11. **Status lines are Hebrew, 3 lines (`done / next / blocked`)** after each deliverable, per `handoff-deliverables.md`. Code, ids, paths stay English.

## Where the detail lives

| Read when | File |
|---|---|
| Building or checking a SEED; the pipeline flowchart | [seed-and-pipeline.md](seed-and-pipeline.md) |
| Steps 1–4: initial plan, bucketing, routing | [steps-1-4.md](steps-1-4.md) |
| Steps 5–6: gate details, doc-sync checklist and tense rule | [gate-and-docsync.md](gate-and-docsync.md) |
| Escalation recursion, delegation modes | [escalation-delegation.md](escalation-delegation.md) |
| Red flags (rationalizations) and cross-references | [red-flags-and-refs.md](red-flags-and-refs.md) |
