# work-kickoff — Steps 1–4: normalize, plan, bucket, route

> Detail for [SKILL.md](SKILL.md). On conflict, SKILL.md §Hard rules wins.

### Step 1 — Normalize
Build the SEED per [seed-and-pipeline.md](seed-and-pipeline.md).
For a `deliverable` seed, print the `V3 › Doc map` and `V3 › Readiness` nodes with a scoped outline script; never dump the whole map.

### Step 2 — Initial plan
Read `origin` + each item's `artifacts`. Produce a short work-unit list. Do NOT design or write code yet.
For the full challenge the units are the five `ex.md` deliverables in handoff order: DESIGN.md → architecture diagram → flow diagram → code → reproducible environment.

### Step 3 — Bucket
Classify every work unit into **design / plan / inline** using [`../_shared/bucket-rubric.md`](../_shared/bucket-rubric.md).
Present the bucketed table and pause for confirmation in non-auto modes.

**Split "doc only" from code before bucketing.** Anything the time box cannot afford (ledger, overlay Flow D, enrichment plugin logic, monitoring) ships as a Protocol stub plus a comment or a DESIGN.md line.
Bucket the stub as `inline`; the prose rides in the DESIGN.md unit.

### Step 4 — Route (per bucket)
- **design** → stop; report the V3 node and the D-xx it conflicts with; ask Ofek one multiple-choice question. The answer re-enters as a `task` seed.
- **plan** → `writing-plan` → execute via `recursive-execution` (≥2 deliverables in one plan) or `superpowers:executing-plans` (flat).
- **inline** → do it directly, no plan doc.
