# Handoff: produce all deliverables for the Technology Entity Disambiguation challenge

## Role and goal
You are implementing a locked design. Produce every deliverable in `ex.md` from `ex.mmap` › `Design > V3 (locked, 22-10-26)`. Do not reopen decisions. A missing or contradicting decision is a **design bucket**: stop, report the V3 node and the D-xx, ask Ofek one multiple-choice question. Never edit `ex.mmap`.

## Entry point (mandatory)
`Invoke the Skill tool with skill='work-kickoff' before doing anything else.`

SEED for the full challenge:
```
{ kind: deliverable, origin: "ex.md › Deliverables 1–5 + this file",
  items: [ D1 DESIGN.md, D2 architecture diagram, D3 flow diagram, D4 code, D5 reproducible environment ] }
```
Each item's artifacts = its row in §Deliverables below + the `V3 › Doc map` nodes that feed it.

The chain `work-kickoff` walks (defined in `.claude/skills/_shared/sdlc-chain-map.md`):
`work-kickoff` → bucket (all five are `plan`) → `writing-plan` (one file: `challange/docs/plans/deliverables.plan.md`) → `recursive-execution` → `superpowers:verification-before-completion` → `superpowers:requesting-code-review` → `session-retrospective`.

Per-leaf first-step lines, gates and commit rules come from `.claude/skills/_shared/` (`tdd-routing.md`, `greenness-ladder.md`, `executor-overrides.md`). Do not restate them here; inline them into subagent prompts as those files say.

## Environment facts the skills assume but the folder lacks (fix before the first leaf, inline bucket)
| Gap | Action |
|---|---|
| No git repository in `/Users/ofeki/works/mars-security` | `git init` at the repo root, first commit `chore(repo): add challenge brief, locked map and handoff` with `challange/ex.md`, `challange/ex.mmap`, `challange/handoff-*.md`, `.claude/`. Leaf commits need it. |
| No root `CLAUDE.md` | Create a 15-line one: stack, time box, `make` targets, the map rule, pointer to `.claude/skills/_shared/`. The doc-sync step expects it. |
| `recursive-execution` and `session-retrospective` | Installed in `.claude/skills/`. Executor = `recursive-execution` (deliverables are internal nodes); `superpowers:executing-plans` only if the plan collapses to one flat group. Run `session-retrospective` at close. |

## Files (folder: `/Users/ofeki/works/mars-security/challange/`)
- `ex.md`: the brief. The only source of requirements. Read first.
- `ex.mmap`: Mind Elixir JSON, root `data.nodeData`. Read with a scoped Python + json outline script, one node path at a time (~1,400 nodes, never dump it): 
  - `Design > V3 (locked, 22-10-26)`: sections 1–13, `Doc map`, `Readiness`.
  - `Brainstorm > V2 > 8. Decisions log`: D-01…D-47, each note has `Why:` and `Evidence:`.
  - `Brainstorm > V2 > 7. Test-case bank`: 25 cases, become tests 1:1, each test cites its node.
  - `Brainstorm > V2 > 0. Inputs & constraints > Measured facts 📊`: numbers for the doc, computed in a sandbox. Quote with `[CONFIRM]` or re-run the method in the note.

## Locked constraints (from V3; do not change)
- Python 3.12, pytest + hypothesis, rapidfuzz, sqlite3 stdlib, Pydantic at file boundaries only (D-46).
- Dictionary-first, deterministic. No LLM, embeddings or RAG anywhere in the resolve path (D-01, D-23).
- Determinism: frozen snapshot holding IDF, thresholds and calibration; `index_version` = content hash (D-12, D-22); tie-break (score desc, entity_id asc) (D-16).
- Interface: `resolve(name: str, *, hints=None, filters=None) -> Resolution`, fields `{id, canonical_name, vendor, category, confidence, status: resolved|ambiguous|no_match, alternatives[], index_version}` (D-18, V3 › 6).
- Scoring: exact alias → base by match type 1.0 / 0.97 / 0.9 / 0.8 weak-unique (D-27); else IDF token-set Jaccard with coverage penalty (D-21); typo = trigram candidates + Levenshtein ≤ 2, ≤ 3 chars exact only (D-26). Decide on (s1, margin) with T_high 0.75, T_low 0.5, M 0.15, K 20, all read from the snapshot, never literals (D-28). Hint bonus +0.15 (D-29).
- Near-collision: product-only alias shared by several vendors → `ambiguous` with alternatives (`Sentinel`); vendor-qualified input → resolved (`Microsoft Sentinel`); weak unique alias → resolved at 0.8 (`EKS`) (D-09, D-27).
- Unknown input → `no_match`, `canonical_name=None`, confidence 0, review-queue stub (D-47).
- Build-time denormalized aliases: parent-vendor × product, category-label × product. Runtime decompose = vendor longest-prefix only, no tree walk (D-44).
- Canonical format `<Vendor> <Product>`; ID = `vendor/product` ascii slug, immutable (D-33).
- Source files: `categories.yaml` (23 leaves, D-34), `vendors.csv`, `entities.jsonl`, `aliases.csv` (D-42). Seed 100–300 entities (D-43).
- Doc only, stubbed with a Protocol or comment: durable ledger (D-30), Flow D overlay (D-43), enrichment plugins (D-37), index health SLOs (D-39), REST, Wikidata / purl / Repology joins.

## Deliverables and done criteria (rows are the SEED items)
| # | Deliverable | Output | Done when |
|---|---|---|---|
| D1 | Design doc | `DESIGN.md` | ≤ ~600 words, one heading per `ex.md` › Deliverable 1 bullet, fed by `V3 › Doc map`, trade-offs cite D-xx inline, 📊 numbers carry `[CONFIRM]` |
| D2 | Architecture diagram | `docs/architecture.{excalidraw,png}` (Mermaid in `DESIGN.md` if the canvas is unavailable) | components from `V3 › 11`; flows A (add/update) and B (resolve) from `V3 › 2` |
| D3 | Flow diagram | `docs/resolve-flow.{excalidraw,png}` | input → normalize → exact alias → decompose → candidates → score → decide → canonical ID, from `V3 › 6` |
| D4 | Code | `src/{constants,models,normalize,build,resolver,ports,cli,eval}.py`, `src/data/*`, `tests/*`, `pyproject.toml` | `make test` N/N ✅; 25 bank cases + leave-one-out + synthetic typos + hypothesis properties (idempotency, casing / punctuation / version invariance, `resolve(canonical) == canonical`); CLI `idx build | validate | resolve | eval | add-alias`; stubs: `ResponseLedger`, `EnrichmentPlugin` Protocols, monitoring / review-queue / Flow D comments |
| D5 | Reproducible environment | `Makefile` (`setup / test / resolve NAME=... / eval`), `Dockerfile` `python:3.12-slim`, `README.md` with 3 commands | `make test && docker build -t tech-resolver .` green; `docker run --rm tech-resolver idx resolve "AWS"` prints a `Resolution` |

Leaf order inside D4 and the env-last rule: `.claude/skills/writing-plan/task-structure.md`. D5 may merge into D4 as its last 🏁 leaf.

Behaviour gate before D4 closes (paste the output):
```bash
make resolve NAME="Amazon Web Services"   # same canonical as "AWS"
make resolve NAME="Sentinel"              # ambiguous + alternatives (D-09)
make resolve NAME="AWS EKS"               # != "Amazon Web Services" (D-10)
make resolve NAME="AWS EKS" && make resolve NAME="AWS EKS"   # identical output, same index_version
```

## Rules
- Reply to Ofek in Hebrew; code, ids, paths and the deliverables in English. After each deliverable: 3 lines `done / next / blocked`.
- Functions 10–20 lines, no comments except the production stubs the brief asks for, no `Any`, no magic numbers.
- Time box 3–4 h total. Anything beyond the brief's tests is doc only.
- `ex.mmap` is Ofek's. Report gaps; never patch the map.
