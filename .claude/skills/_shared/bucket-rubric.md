# Bucket rubric (shared) — one classification for all seeds

Every unit of work (a deliverable, an ad-hoc task, a bug) classifies into **exactly one** of three buckets.

## Decision table

Classify by asking, in order — first match wins:

| Ask | If yes → bucket |
|---|---|
| Needs a design decision not locked in `ex.mmap` V3, a new interface/contract, or a change to a D-xx decision? | **design** |
| Multi-file, approach is clear from V3, needs an ordered plan to ship safely (any `ex.md` deliverable)? | **plan** |
| Small, mechanical, single- or few-file, no design decision, ships in one commit? | **inline** |

If a unit is ambiguous between two buckets, pick the **heavier** one (design > plan > inline).
The cost of over-scoping is one extra plan section; the cost of under-scoping is a mid-flight halt.

## Route per bucket

| Bucket | Route to | Then |
|---|---|---|
| **design** | report the gap (node + conflicting D-xx) and ask Ofek one multiple-choice question; `hld` / `system-design-process` only if he asks for a design pass | re-classify the answer into `plan` / `inline` and fold back |
| **plan** | `writing-plan` → execute via `recursive-execution` (tree) or `superpowers:executing-plans` (flat) | — |
| **inline** | do it directly (no plan doc) | still TDD + green gate |

## Invariants (true for every bucket)

- **Always TDD** — route by scope via [`tdd-routing.md`](tdd-routing.md); even an `inline` quick-fix writes the failing test first.
- **Always pass the green gate** — [`greenness-ladder.md`](greenness-ladder.md) (`inline`/leaf → `guard`; task-done → `verify`; 🏁 deliverable → `sweep`).
- **Never edit `ex.mmap`.** A design bucket produces a question, not a map edit.
