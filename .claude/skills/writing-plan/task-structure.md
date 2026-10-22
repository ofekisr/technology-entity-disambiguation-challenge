# writing-plan — Task structure

> Detail for [SKILL.md](SKILL.md). On conflict, SKILL.md §Hard rules wins.

## Task structure (one task per leaf — deliverable = virtual PR, leaf = one commit)

> **Tasks = leaves. Each leaf = one commit**, committed by the leaf's own subagent after `guard` passes (`make test` + extra gate at 🏁).
>
> An `ex.md` deliverable is a **virtual PR** — a coherent grouping that must ship green together. **A deliverable is not a commit.** The planner expands each into leaves ordered bottom-up by dependency. Task count = leaves + one review task per deliverable + the verification task.

Canonical source: [`../_shared/executor-overrides.md`](../_shared/executor-overrides.md) + [`../_shared/greenness-ladder.md`](../_shared/greenness-ladder.md).

### Deliverables → task groups in the one plan

Each `ex.md` deliverable becomes a **task group**: a `### D<n> <name>` sub-heading, its leaves in DAG order, ending in that group's 🏁 leaf, then its review task. Groups follow handoff order: D1 DESIGN.md → D2 architecture diagram → D3 flow diagram → D4 code → D5 environment. `## Deliverable mapping` lists group → task range. `recursive-execution` runs each group as an internal node.

A docs or diagram deliverable is usually an **atomic group**: one leaf, marked 🏁, then its review task.

### Canonical leaf order within the code deliverable (bottom-up DAG)

1. **Constants / types** — canonical-name rules (D-33), status enum, match-type bases (1.0 / 0.97 / 0.9 / 0.8), no thresholds here (they live in the snapshot).
2. **Pydantic boundary models** — `entities.jsonl`, `aliases.csv`, `vendors.csv`, `categories.yaml` rows + `Resolution` (D-18, D-46).
3. **Seed data files** — `src/data/*` (100–300 entities, D-43; 23 category leaves, D-34) + a loader test.
4. **Test bank** — the 25 cases as parametrized tests, red (cites `7. Test-case bank`).
5. **Normalize** — casing / punctuation / version stripping; property tests for invariance.
6. **Build (Flow A)** — `build.py` → `snapshot.sqlite` with IDF, thresholds, calibration, `index_version` = content hash (D-12, D-22, D-44 denormalized aliases).
7. **Resolver (Flow B)** — exact alias → vendor longest-prefix decompose → trigram candidates → IDF Jaccard + Levenshtein → `(s1, margin)` decision → tie-break (D-16, D-21, D-26–29, D-47). Turns the bank green.
8. **Ports** — `ResponseLedger`, `EnrichmentPlugin` Protocols + in-memory stubs with the production-concern comments `ex.md` asks for.
9. **CLI** — `idx build | validate | resolve | eval | add-alias`.
10. **Eval** — gold set, threshold sweep, calibration buckets, F1 / p50 / p99 / cost per 1M.
11. **Makefile + Dockerfile + README** — LAST leaf, 🏁 (this is also D5 when the plan merges D4/D5; otherwise D5 is its own atomic group).

**Contract rule.** `Resolution` and the snapshot schema are contracts: their full shape lands in leaf 2 / leaf 6 **before any consumer**. No leaf commits `Any`, `object`, or a partial model for a contract another task owns.

### Atomic-group exception

A deliverable that is genuinely one leaf (DESIGN.md, one diagram, a single-file refactor) stays one task marked 🏁. Do not split it into "scaffold + fill".

### 🏁 marker

Mark the **LAST leaf of each deliverable** with 🏁 in the heading, e.g.:

```
## Task 14 — chore(env): add Makefile, Dockerfile and README [code] 🏁
```

At a 🏁 leaf: `make test` + the deliverable's extra gate ([`../_shared/greenness-ladder.md`](../_shared/greenness-ladder.md)); the next task is the review task; the mode-driven approval gate fires after that review.

### Review task (one per deliverable, immediately after its 🏁 leaf)

````markdown
## Task N — review(D<n> <name>): quality + fidelity

**Files:** none — read-only. Findings route back to Tasks <a>–<b>.

**Required skill (first step):** Invoke the Skill tool with skill='superpowers:requesting-code-review' before doing anything else. The controller runs this task itself and dispatches one reviewer as a `model: 'sonnet'` subagent; no implementer subagent, no commit.

- [ ] **Step 1: Reviewer.** `BASE_SHA` = the commit before Task <a>'s commit, `HEAD_SHA` = Task <b>'s commit, `{PLAN_OR_REQUIREMENTS}` = Tasks <a>–<b> above + the `ex.md` deliverable bullets. Verdict in two halves — **fidelity:** every committed change traces to a task step, every step has a change, every D-xx the task text names is implemented as locked; **quality:** functions 10–20 lines, no `Any`, no magic thresholds, no comments beyond production stubs, Pydantic only at file boundaries, deterministic tie-break.
- [ ] **Step 2: Route findings.** Each finding reopens its leaf: fix, re-run that leaf's gate, commit `fix(<scope>): <finding>`, then re-run Step 1. Record `review: ✅` here when it passes.
````

### Per-task shape

````markdown
## Task N — <one-line description; matches the commit subject> [code|docs|diagram]

**Files:**
- Create: <path> | Modify: <path>     (only files this task touches)

**Design:** V3 §<n> · D-xx, D-yy

**Required skill (first step):** Invoke the Skill tool with skill='<skill-name>' before doing anything else.

- [ ] **Step 1: <verb-led action>**
  <inline code/command and concrete expected output>

- [ ] **Step N: Commit** (subagent commits its own leaf, after the greenness gate passes)
  ```bash
  git add <explicit paths — no glob>
  git commit -m "<prewritten conventional commit message>"
  ```
````

Required-skill selection follows the task's scope tag per [`../_shared/tdd-routing.md`](../_shared/tdd-routing.md).

### Bug-fix plan shape (when `TDD scope: bug-fix`)

**Task 1 — Phase A: Inspection** (read-only, no commit). First step: `Invoke the Skill tool with skill='superpowers:systematic-debugging' before reproducing. This task is READ-ONLY — do not edit code or commit. Return a verdict block only.` Steps: reproduce with the exact `make resolve` / `pytest` command; classify the existing test `MISSING | WRONG | REDUNDANT | CORRECT-BUT-RED`; emit `{root_cause, test_classification, proposed_action, files_touched_in_phase_b}`.

**Task 2 — Phase B: Adapt** (write-capable). First step: `superpowers:test-driven-development`. Branches: `MISSING` / `CORRECT-BUT-RED` → TDD, one commit `fix(<scope>): <summary>`; `WRONG` → `test(<scope>): correct <test>` then `fix(<scope>): …`; `REDUNDANT` → `test(<scope>): remove duplicate <test>` first.

**Task 3** — the review task. No 🏁, no leaf-DAG.

### Per-step rules

- **One logical action per step.** "Write the failing test" is one step. "Run the test, expect failure" is one step.
- **Inline code or command for every step.** No "similar to…", no "TBD".
- **Expected output on every step that runs anything.** `N passed`, a `Resolution` dict, a file list, an image path.
- **The last step of every leaf task is the commit step.** `git add` lists explicit paths. Message prewritten; do not paraphrase.
- **🏁 leaves carry the boundary work** (`make test` + extra gate); non-🏁 leaves run only `guard`.

### Commit message rendering

- **Type** — `feat` new surface, `fix` bug, `chore` tooling / data / env, `test` test-only, `docs` docs-only, `refactor` non-behavioral.
- **Scope** — the module: `data`, `normalize`, `build`, `resolver`, `ports`, `cli`, `eval`, `env`, `design`, `diagram`.
- **Subject** — short, imperative, no period.
