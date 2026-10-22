---
name: writing-plan
description: "Use when the design in ex.mmap V3 is locked and you are about to hand implementation to an executor, and the work spans more than one trivial commit — turns the ex.md deliverables into one ordered, commit-by-commit plan."
---

# Writing Plan (project-local)

Converts the locked design (`ex.mmap` › `Design > V3`) plus the `ex.md` deliverables into the single artifact an executor (subagent or human) reads to ship the work: a plan file at `challange/docs/plans/<slug>.plan.md`, encoded so it survives separation from CLAUDE.md. Why this exists: [rationale.md](rationale.md).

## When to Use

- V3 is locked (`V3 › Readiness` has no blocking ❗) and you are about to hand work to an executor.
- **One challenge → one plan file**, covering every `ex.md` deliverable. Deliverables become task groups inside the one plan (see [task-structure.md](task-structure.md)).

## When NOT to Use

- A V3 decision is missing or contradicts `ex.md` → stop, report, ask Ofek one multiple-choice question. Never invent a decision.
- The work is a one-step trivial change (single commit, no orchestration). Skip; just do the work.
- The plan exists already and is being amended mid-execution → edit the file directly; do not regenerate. Honor [approval-and-amending.md](approval-and-amending.md).

## Input contract

You need four inputs before writing a single line:

1. **`ex.md`** — every deliverable and every required behaviour (aliases, near-collisions, hard negatives, idempotency, production-concern stubs, run instructions).
2. **`ex.mmap` › `Design > V3 (locked)`** sections 1–13, `Doc map`, `Readiness`; **`Brainstorm > V2 > 8. Decisions log`** D-xx; **`7. Test-case bank`** (25 cases → tests 1:1). Read with a scoped outline script; never dump the map.
3. **`handoff-deliverables.md`** — the file layout (`src/data/`, `build.py`, `resolver.py`, `cli.py`, `eval.py`, `ports.py`, `tests/`), the locked constraints, the done criteria.
4. **Project CLAUDE.md invariants** — code conventions, time box. Encode only the ones that change executor behavior into the plan header.

If any input is missing or partial → walk the question ladder ([`../_shared/executor-overrides.md`](../_shared/executor-overrides.md) §Asking the user is the last resort). Never invent file paths, thresholds, seed-file columns, or commit messages.

**Output:** one file at `challange/docs/plans/<slug>.plan.md`. Sections in order: header block → File Map → tasks → Self-review checklist → optional Open items deferred / Deliverable mapping. Skeleton + File Map rules: [output-format.md](output-format.md).

## Mandatory header block (load-bearing)

> **Single source of truth for the override sentence + routing lines:** [`../_shared/executor-overrides.md`](../_shared/executor-overrides.md), [`../_shared/greenness-ladder.md`](../_shared/greenness-ladder.md), [`../_shared/tdd-routing.md`](../_shared/tdd-routing.md). The header text below encodes them into the plan artifact; keep it in sync.

These lines MUST appear at the top of every plan file, before any task, in this order:

1. **Title** — `# <slug> — <descriptive title> (Implementation Plan)`.
2. **Required sub-skill banner** — verbatim:
   > `> **For agentic workers:** REQUIRED SUB-SKILL: Use \`recursive-execution\` (multi-deliverable tree, default) or \`superpowers:executing-plans\` (flat) to implement this plan task-by-task.`
3. **CLAUDE.md override sentence** — verbatim:
   > `CLAUDE.md override: the leaf-executing subagent commits its own leaf after the greenness gate passes (\`python -m pytest -q tests/<file>\` for a leaf; \`make test\` + the deliverable's extra gate at 🏁 leaves; \`make test && docker build\` once, in the final verification task). Reviews (code-quality + fidelity to the task text) are explicit review tasks in this plan — one reviewer, one task immediately after each 🏁 leaf — run by the controller; never per leaf, never only at the end. After every leaf commit the controller checks the commit's shape (\`git show --stat\` against the task's Files list and prewritten message), never its diff. Approval-gate tier follows the active Claude Code mode (default = per-leaf pause, auto-accept-edits = per-deliverable pause, auto-mode/yolo = no pause). Never edit \`ex.mmap\`.`
4. **`**Status:**`** — `✅ ready` / `🔒 blocked (waiting <X>)`.
5. **`**Spec:**`** — `ex.md` deliverable sections + the `V3 › Doc map` and `Readiness` node paths.
6. **`**Goal:**`** — one paragraph: what ships at the end. Concrete (`make test` N/N, `docker build` green, `DESIGN.md` one page, two diagrams, CLI resolves the four `ex.md` behaviours).
7. **`**Architecture:**`** — one paragraph: the named patterns this plan applies, each citing its D-xx (dictionary-first D-01, frozen snapshot D-12/D-22, scoring D-21/D-26–28, decomposition D-44, `no_match` D-47).
8. **`**Tech Stack:**`** — one line: Python 3.12, pytest + hypothesis, rapidfuzz, sqlite3, Pydantic, Make, Docker `python:3.12-slim`.
9. **`**Source design:**`** — `ex.mmap` node paths for every V3 section and D-xx the plan references.
10. **`**TDD scope:**`** — `code` | `docs` | `diagram` | `bug-fix` | `mixed` (per [`../_shared/tdd-routing.md`](../_shared/tdd-routing.md)). The full challenge is `mixed`: tag each task heading `[code]` / `[docs]` / `[diagram]`; the task's first-step line follows its tag.
11. **`**Time box:**`** — per deliverable, summing to 3–4 h (e.g. DESIGN.md 45 min, diagrams 30 min, code 2 h, env 20 min, review 15 min).

If any of items 2–11 is missing, the plan is malformed. Do not ship.

## Hard rules

1. **Tasks = leaves, one leaf = one commit.** A deliverable is a virtual PR, not a commit: expand each into leaves. Task count = leaves across all deliverables + one review task per deliverable + the final verification task.
2. **Leaf order is the bottom-up DAG** within the code deliverable: constants/types → Pydantic boundary models → seed data files → normalize → build (snapshot) → resolver → ports stubs → cli → eval → Makefile/Dockerfile **LAST**. No leaf imports a file that does not exist yet, and no leaf commits a placeholder for a contract another task owns.
3. **🏁 marks the last leaf of every deliverable.** Its gate is `make test` + the deliverable's extra gate; the very next task is that deliverable's review task (`review(<deliverable>): quality + fidelity`, one `sonnet` reviewer, controller-run, ends in a verdict, never commits). Non-🏁 leaves run only `guard`.
4. **The subagent commits its own leaf** after its gate passes. The commit step is the last step, `git add` lists explicit paths, and the message is prewritten per leaf, conventional `type(scope): subject`.
5. **First-step skill lines are verbatim** from [`../_shared/tdd-routing.md`](../_shared/tdd-routing.md). `bug-fix` scope = Task 1 Phase A inspection → Task 2 Phase B adapt → Task 3 review. No leaf-DAG, no 🏁.
6. **Every step is one action with inline code or a command and its expected output.** No "TBD", no "similar to…"; if you cannot fill it in, V3 is not refined enough — report the gap.
7. **The 25 test-bank cases are tests 1:1** and land in the first test leaf of the code deliverable, before the resolver exists. Each case cites its bank node.
8. **The final task is always `Verification + companion-doc surface`** (`superpowers:verification-before-completion`): `make test` N/N, `docker build`, the four CLI behaviours, `DESIGN.md` one page, `README.md` 3 commands, `V3 › Readiness` re-check, then re-read `ex.md` and map each deliverable bullet to file:line. Flip to `✅ complete` only if zero criteria are unmet.
9. **Ship the Self-review checklist unticked**; the verification task re-runs and ticks it. Every `- [ ]` needs an owner and a tick-moment.
10. **A task added after a verification ran revokes it:** untick the verification steps and affected checklist boxes, downgrade status to `🟡 in progress`. Never grandfather.
11. **Cite V3 sections and D-xx by node path** for every decision; never re-render CLAUDE.md rules in the plan body beyond header items 2–3.

## Approval Protocol

Run the spec-review gate (detail: [approval-and-amending.md](approval-and-amending.md)), then emit:

> ⏸️ WAIT — Review plan. Say 'ok' to hand off to executor, or provide feedback.

**Yolo scope:** `yolo plan` skips approval within this plan-writing session. Still HALT if V3 has a blocking ❗ or if any required header item is missing.

## Where the detail lives

| Read when | File |
|---|---|
| Laying out the file skeleton, the File Map, or test-command blocks | [output-format.md](output-format.md) |
| Ordering leaves, writing a task/review/bug-fix block, step rules, commit messages | [task-structure.md](task-structure.md) |
| Writing the final verification task | [verification-task.md](verification-task.md) |
| Writing the Self-review checklist into the plan | [self-review-checklist.md](self-review-checklist.md) |
| Spec-review gate, amending a plan, optional final sections | [approval-and-amending.md](approval-and-amending.md) |
| Why this skill exists, the stop list, cross-references | [rationale.md](rationale.md) |

Chain: [`../_shared/sdlc-chain-map.md`](../_shared/sdlc-chain-map.md). Upstream: `ex.mmap` V3. Downstream: `recursive-execution` / `superpowers:executing-plans`.
