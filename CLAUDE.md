# mars-security — Technology Entity Disambiguation challenge

- **Brief:** `challange/ex.md` (only source of requirements). **Locked design:** `challange/ex.mmap` › `Design > V3 (locked, 22-10-26)` + `Brainstorm > V2 > 8. Decisions log` (D-01…D-47).
- **Map rule:** never edit `challange/ex.mmap`. Read it with a scoped Python + json outline (one node path at a time). A missing or contradicting decision → stop, cite the V3 node + D-xx, ask Ofek one multiple-choice question.
- **Stack:** Python 3.12, pytest + hypothesis, rapidfuzz, sqlite3 stdlib, Pydantic at file boundaries only (D-46). No LLM / embeddings / RAG in the resolve path (D-01, D-23).
- **Time box:** 3–4 h total. Anything beyond the brief's tests is doc only (stub Protocol or a `challange/docs/DESIGN.md` line).
- **Make targets** (run from `challange/`): `make setup`, `make test`, `make resolve NAME="..."`, `make eval`. Docker: `docker build -t tech-resolver .`
- **Plan:** `challange/docs/plans/deliverables.plan.md` — one leaf = one commit, conventional messages.
- **Code rules:** functions 10–20 lines, no `Any`, no magic numbers (thresholds live in the snapshot), no comments except production stubs, tie-break `(score desc, entity_id asc)`.
- **Process detail:** `.claude/skills/_shared/` (`greenness-ladder.md`, `tdd-routing.md`, `executor-overrides.md`, `sdlc-chain-map.md`).
- **Status lines to Ofek:** Hebrew, 3 lines `done / next / blocked`; code, ids and paths in English.
