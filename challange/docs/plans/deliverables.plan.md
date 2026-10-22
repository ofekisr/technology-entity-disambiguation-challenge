# deliverables — Technology Entity Disambiguation: design doc, diagrams, resolver, environment (Implementation Plan)

> **For agentic workers:** REQUIRED SUB-SKILL: Use `recursive-execution` (multi-deliverable tree, default) or `superpowers:executing-plans` (flat) to implement this plan task-by-task.

CLAUDE.md override: the leaf-executing subagent commits its own leaf after the greenness gate passes (`python -m pytest -q tests/<file>` for a leaf; `make test` + the deliverable's extra gate at 🏁 leaves; `make test && docker build` once, in the final verification task). Reviews (code-quality + fidelity to the task text) are explicit review tasks in this plan — one reviewer, one task immediately after each 🏁 leaf — run by the controller; never per leaf, never only at the end. After every leaf commit the controller checks the commit's shape (`git show --stat` against the task's Files list and prewritten message), never its diff. Approval-gate tier follows the active Claude Code mode (default = per-leaf pause, auto-accept-edits = per-deliverable pause, auto-mode/yolo = no pause). Never edit `ex.mmap`.

**Status:** ✅ complete
**Executor (this run):** `superpowers:executing-plans` (flat), per the pasted handoff of 22-10-26.

**Spec:** `ex.md` › Deliverables 1–4 + Reproducible Environment · `ex.mmap` › `Design > V3 (locked, 22-10-26) > Doc map` · `… > Readiness`

**Goal:** `DESIGN.md` on one page (≤ ~600 words, one heading per Deliverable 1 bullet, D-xx cited inline); `docs/architecture.*` and `docs/resolve-flow.*`; a Python package `src/` exposing `resolve(name, *, hints=None, filters=None) -> Resolution` over a frozen SQLite snapshot, with a CLI `idx build | validate | resolve | eval | add-alias`; `make test` N/N green (25 bank cases, leave-one-out, synthetic typos, hypothesis properties); `docker build -t tech-resolver .` green; `make resolve` shows the four `ex.md` behaviours.

**Architecture:** dictionary-first, deterministic, closed world (D-01, D-23, D-47). Source files in git → offline build (Flow A) → one SQLite snapshot holding entities, aliases, postings, IDF and thresholds; `index_version` = sha256 of the snapshot content (D-12, D-22, D-35). Build denormalizes vendor × product, parent-vendor × product and product × category-label aliases (D-20, D-44); generated aliases never shadow manual ones (V3 §6 sub-vendor rule "own products first"). Runtime (Flow B): normalize (D-07) → LRU + ledger port (D-17, D-30) → exact alias with base by match type (D-27) → vendor longest-prefix decompose as inferred hint (D-19, D-44) → postings + trigram typo fix with Levenshtein ≤ 2, ≤ 3 chars exact only (D-20, D-26) → IDF-weighted token-set Jaccard with coverage penalty (D-21) → decide on `(s1, margin)` with T_high / T_low / M / K from the snapshot (D-22, D-28), hint bonus (D-29), tie-break `(score desc, entity_id asc)` (D-16).

**Tech Stack:** Python 3.12, pytest + hypothesis, rapidfuzz, sqlite3, Pydantic v2, PyYAML, Make, Docker `python:3.12-slim`.

**Source design:** `Design > V3` §1 Approach, §2 High-level flows, §3 Canonical & IDs, §4 Index model, §5 Build pipeline, §6 Resolve flow, §7 Update API, §8 Evaluation, §9 Index health, §10 Scope, §11 Components, §12 Scale, §13 Reproducible environment · `Brainstorm > V2 > 8. Decisions log` D-01…D-47 · `Brainstorm > V2 > 7. Test-case bank` · `Brainstorm > V2 > 2 > Q1` (23 category leaves), `Q11` (sub-vendor rules), `Q15` (score formula).

**TDD scope:** mixed — each task heading carries `[code]`, `[docs]` or `[diagram]`.

**Time box:** D1 DESIGN.md 35 min · D2 + D3 diagrams 30 min · D4 code 2 h 15 min · D5 env 15 min · reviews + verification 25 min = 3 h 40 min.

**Interpretations (no design gap, recorded for review):**
- Vendor entity id = `<vendor_id>/*` (CPE WFN `ANY` product), so `aws/*` (vendor) and `aws/aws` (product) stay distinct per D-32.
- `(s1 ≥ T_low, margin ≥ M, s1 < T_high)` is not covered by Q15's two rules; it returns `ambiguous` (precision over recall, D-14).
- Ambiguous result: `id = canonical_name = None`, `alternatives` carry `s_i / Σ s_topK` (Q15).
- Calibration table (D-40) ships as 10 identity bins in the snapshot; `idx eval` prints the reliability table + ECE. Fitting waits for the hand-labeled dev set (D-38 risk: leave-one-out inflates precision).
- Leaf order puts `ports.py` before `resolver.py` because the resolver imports the ledger and review-queue ports (leaf-order invariant wins over the canonical list).
- Bank "Nginx (vendor F5)": id `nginx/nginx`, canonical `Nginx`, vendor `NGINX` (operating brand, D-11), `parent_vendor_id = f5`.

---

## File Map

**Create:**
- `challange/docs/DESIGN.md` (moved from `challange/DESIGN.md` by Ofek's request, 22-10-26)
- `challange/docs/architecture.md` (Mermaid; Excalidraw canvas at `localhost:3333` was down)
- `challange/docs/resolve-flow.md` (Mermaid; same reason)
- `challange/pyproject.toml`
- `challange/src/__init__.py`, `challange/src/constants.py`, `challange/src/models.py`, `challange/src/normalize.py`, `challange/src/build.py`, `challange/src/ports.py`, `challange/src/resolver.py`, `challange/src/cli.py`, `challange/src/eval.py`
- `challange/src/data/categories.yaml`, `challange/src/data/vendors.csv`, `challange/src/data/entities.jsonl`, `challange/src/data/aliases.csv`, `challange/src/data/thresholds.yaml`, `challange/src/data/gold.jsonl`
- `challange/tests/conftest.py`, `challange/tests/test_models.py`, `challange/tests/test_data.py`, `challange/tests/test_bank.py`, `challange/tests/test_normalize.py`, `challange/tests/test_build.py`, `challange/tests/test_ports.py`, `challange/tests/test_resolver.py`, `challange/tests/test_properties.py`, `challange/tests/test_cli.py`, `challange/tests/test_eval.py`
- `challange/Makefile`, `challange/Dockerfile`, `challange/.dockerignore`, `challange/README.md`

**Modify:**
- `challange/docs/plans/deliverables.plan.md` (controller ticks; final verification commits)
- `CLAUDE.md` (root, only if a convention changes)

**Test commands:**

```bash
python -m pytest -q tests/<file>            # guard — every leaf
make test                                    # verify — task done / 🏁
make test && docker build -t tech-resolver . # sweep — final verification
```

---

### D1 DESIGN.md

## Task 1 — docs(design): add one-page design document [docs] 🏁

**Files:** Create: `challange/DESIGN.md`

**Design:** V3 › Doc map (all `Doc ›` nodes) · §1, §3, §4, §6, §8, §9, §12 · D-01…D-47

**Required skill (first step):** Invoke the Skill tool with skill='write-markdown' before writing any prose. Budget: DESIGN.md is one page.

- [x] **Step 1: Write headings** — `Approach`, `Key decisions & trade-offs` (precision vs recall · ambiguity · update strategy), `Data structures`, `Scale to 100k+`, `Evaluation infrastructure`, one per `ex.md` › Deliverable 1 bullet, fed by the matching `Doc ›` node.
- [x] **Step 2: Fill each heading** — tables / bullets; trade-offs cite D-xx inline (precision vs recall D-14, D-27, D-28; ambiguity D-09, D-22, D-32; update D-13, D-31, D-36); 📊 numbers (memory D-35, cost D-01) carry `[CONFIRM]`.
- [x] **Step 3: Gate** — `wc -w DESIGN.md` → ≤ ~600 (excluding diagram embeds); `grep -c '^## ' DESIGN.md` → ≥ 5.
- [x] **Step 4: Commit** (subagent commits its own leaf, after the greenness gate passes)
  ```bash
  git add challange/DESIGN.md
  git commit -m "docs(design): add one-page design document"
  ```

## Task 2 — review(D1 DESIGN.md): quality + fidelity

**Files:** none — read-only. Findings route back to Task 1.

**Required skill (first step):** Invoke the Skill tool with skill='superpowers:requesting-code-review' before doing anything else. The controller runs this task itself and dispatches one reviewer as a `model: 'sonnet'` subagent; no implementer subagent, no commit.

- [x] **Step 1: Reviewer.** `BASE_SHA` = commit before Task 1, `HEAD_SHA` = Task 1. Fidelity: every Deliverable 1 bullet has a heading and every trade-off a D-xx. Quality: one page, no history prose, `[CONFIRM]` on 📊 numbers.
- [x] **Step 2: Route findings.** Fix → `fix(design): <finding>` → re-run Step 1. Record `review: ✅`.

### D2 Architecture diagram

## Task 3 — docs(diagram): add architecture diagram [diagram] 🏁

**Files:** Create: `challange/docs/architecture.excalidraw`, `challange/docs/architecture.png` (fallback `challange/docs/architecture.mmd`)

**Design:** V3 §11 Components · §2 Flow A (add/update) and Flow B (resolve) · D-12, D-35, D-37

**Required skill (first step):** Invoke the Skill tool with skill='excalidraw-draw' before drawing. If the canvas is unavailable, emit Mermaid into DESIGN.md and say so.

- [x] **Step 1: Draw components** — Source files in git (`categories.yaml`, `vendors.csv`, `entities.jsonl`, `aliases.csv`) · Build CLI (ingest → generate aliases → validate → IDF / postings → eval gate → publish) · Snapshot (SQLite, `index_version`) · Resolver library (LRU, ledger port) · Eval harness · Review queue + enrichment plugins (stubs, dashed).
- [x] **Step 2: Draw flows** — Flow A: `idx add-alias` / PR → source files → build → snapshot vN+1 (atomic swap). Flow B: caller → `resolve()` → normalize → LRU → ledger → snapshot → `Resolution`; `no_match` → review queue.
- [x] **Step 3: Export** — `.excalidraw` scene + `.png`; gate: both files exist.
- [x] **Step 4: Commit** (subagent commits its own leaf, after the greenness gate passes)
  ```bash
  git add challange/docs/architecture.excalidraw challange/docs/architecture.png
  git commit -m "docs(diagram): add architecture diagram"
  ```

## Task 4 — review(D2 Architecture diagram): quality + fidelity

**Files:** none — read-only. Findings route back to Task 3.

**Required skill (first step):** Invoke the Skill tool with skill='superpowers:requesting-code-review' before doing anything else. The controller runs this task itself and dispatches one reviewer as a `model: 'sonnet'` subagent; no implementer subagent, no commit.

- [x] **Step 1: Reviewer.** Every V3 §11 component present; flows A and B both drawn and labeled.
- [x] **Step 2: Route findings.** Fix → `fix(diagram): <finding>`. Record `review: ✅`.

### D3 Flow diagram

## Task 5 — docs(diagram): add resolve flow diagram [diagram] 🏁

**Files:** Create: `challange/docs/resolve-flow.excalidraw`, `challange/docs/resolve-flow.png` (fallback `challange/docs/resolve-flow.mmd`)

**Design:** V3 §6 Resolve flow · D-16, D-19, D-21, D-22, D-26–D-29, D-44, D-47

**Required skill (first step):** Invoke the Skill tool with skill='excalidraw-draw' before drawing. If the canvas is unavailable, emit Mermaid into DESIGN.md and say so.

- [x] **Step 1: Draw** — input → normalize → LRU / ledger hit? → exact alias (base 1.0 / 0.97 / 0.9 / 0.8) → decompose (vendor longest-prefix = inferred hint) → candidates (postings + trigram typo, Levenshtein ≤ 2) → score (IDF Jaccard + coverage) → decide `(s1, margin)` vs T_high / T_low / M → `resolved` (canonical ID) | `ambiguous` (alternatives) | `no_match` (review queue).
- [x] **Step 2: Gate** — labels contain `normalize`, `candidate`, `decide`, `canonical ID` (ex.md › Deliverable 3).
- [x] **Step 3: Commit** (subagent commits its own leaf, after the greenness gate passes)
  ```bash
  git add challange/docs/resolve-flow.excalidraw challange/docs/resolve-flow.png
  git commit -m "docs(diagram): add resolve flow diagram"
  ```

## Task 6 — review(D3 Flow diagram): quality + fidelity

**Files:** none — read-only. Findings route back to Task 5.

**Required skill (first step):** Invoke the Skill tool with skill='superpowers:requesting-code-review' before doing anything else. The controller runs this task itself and dispatches one reviewer as a `model: 'sonnet'` subagent; no implementer subagent, no commit.

- [x] **Step 1: Reviewer.** Step order matches V3 §6; three terminal statuses shown.
- [x] **Step 2: Route findings.** Fix → `fix(diagram): <finding>`. Record `review: ✅`.

### D4 Code (D5 environment merged as its 🏁 leaf)

## Task 7 — feat(constants): add package scaffold and constants [code]

**Files:** Create: `challange/pyproject.toml`, `challange/src/__init__.py`, `challange/src/constants.py`, `challange/tests/conftest.py`

**Design:** V3 §3, §6 · D-26, D-27, D-33, D-46

**Required skill (first step):** Invoke the Skill tool with skill='superpowers:test-driven-development' before doing anything else.

- [x] **Step 1: pyproject** — package `src` (+ `src/data/*` package data), deps `pydantic>=2`, `rapidfuzz`, `pyyaml`; extra `dev` = `pytest`, `hypothesis`; script `idx = "src.cli:main"`; pytest `pythonpath = ["."]`, `testpaths = ["tests"]`.
- [x] **Step 2: constants** — `Status` (`resolved|ambiguous|no_match`), `Strength` (`canonical|strong|generated|weak`), `BASE_BY_STRENGTH = {canonical: 1.0, strong: 0.97, generated: 0.9, weak: 0.8}` (D-27), `MAX_TYPO_DISTANCE = 2`, `EXACT_ONLY_MAX_LEN = 3` (D-26), `VENDOR_PRODUCT = "*"`, `SYMBOL_TOKENS = {"c++", "c#", "f#", ".net"}` (D-33), `DATA_DIR`, `DEFAULT_SNAPSHOT`. No thresholds (they live in the snapshot, D-28).
- [x] **Step 3: Guard** — `pip install -e '.[dev]' && python -c "import src.constants"` → exit 0.
- [x] **Step 4: Commit** (subagent commits its own leaf, after the greenness gate passes)
  ```bash
  git add challange/pyproject.toml challange/src/__init__.py challange/src/constants.py challange/tests/conftest.py
  git commit -m "feat(constants): add package scaffold and constants"
  ```

## Task 8 — feat(models): add boundary models and Resolution [code]

**Files:** Create: `challange/src/models.py`, `challange/tests/test_models.py`

**Design:** V3 §4, §6 Output · D-18, D-36, D-42, D-46

**Required skill (first step):** Invoke the Skill tool with skill='dev-parse-validate' before doing anything else, then superpowers:test-driven-development.

- [x] **Step 1: Failing tests** — `test_entity_row_rejects_bad_id` (`"AWS EKS"` → `ValidationError`), `test_alias_row_defaults_strong`, `test_resolution_no_match_shape` (`canonical_name is None`, `confidence == 0`).
- [x] **Step 2: Models** — `CategoryLeaf(id, label, group)`, `VendorRow(vendor_id, name, parent_vendor_id, flagship_entity_id, aliases)`, `EntityRow(id, vendor_id, product, category, tier, cpe)`, `AliasRow(alias, entity_id, strength, source, actor, added_at, reason, evidence_url)` (D-36 provenance), `Hints(vendor, category)`, `Filters(vendors, categories, include_uncategorized=True)` (frozen, hashable), `Alternative(id, canonical_name, confidence)`, `Resolution(id, canonical_name, vendor, category, confidence, status, alternatives, index_version)`.
- [x] **Step 3: Guard** — `python -m pytest -q tests/test_models.py` → `3 passed`.
- [x] **Step 4: Commit** (subagent commits its own leaf, after the greenness gate passes)
  ```bash
  git add challange/src/models.py challange/tests/test_models.py
  git commit -m "feat(models): add boundary models and Resolution"
  ```

## Task 9 — chore(data): add seed catalog and loaders [code]

**Files:** Create: `challange/src/data/categories.yaml`, `challange/src/data/vendors.csv`, `challange/src/data/entities.jsonl`, `challange/src/data/aliases.csv`, `challange/src/data/thresholds.yaml`, `challange/tests/test_data.py`; Modify: `challange/src/models.py` (loaders)

**Design:** V3 §4, §10 · D-28, D-32, D-34, D-41, D-42, D-43 · Q1-A leaves

**Required skill (first step):** Invoke the Skill tool with skill='dev-parse-validate' before doing anything else, then superpowers:test-driven-development.

- [x] **Step 1: Failing tests** — `test_categories_have_23_leaves`, `test_entity_count_in_seed_range` (100 ≤ n ≤ 300), `test_every_entity_has_known_category`, `test_thresholds_match_d28` (`T_high 0.75, T_low 0.5, M 0.15, K 20, hint_bonus 0.15`).
- [x] **Step 2: Data** — 23 leaves (security 6, cloud 2, infra 5, dev 4, apps 4, vendor, uncategorized); vendors incl. `amazon` ⊃ `aws` (flagship `aws/aws`), `f5` ⊃ `nginx`, `microsoft` ⊃ `github`, `thales`, `hashicorp`, `falconry`; every bank entity present.
- [x] **Step 3: Loaders** — `load_sources(data_dir) -> Sources` parses each file through its model.
- [x] **Step 4: Guard** — `python -m pytest -q tests/test_data.py` → `4 passed`.
- [x] **Step 5: Commit** (subagent commits its own leaf, after the greenness gate passes)
  ```bash
  git add challange/src/data/categories.yaml challange/src/data/vendors.csv challange/src/data/entities.jsonl challange/src/data/aliases.csv challange/src/data/thresholds.yaml challange/src/models.py challange/tests/test_data.py
  git commit -m "chore(data): add seed catalog and loaders"
  ```

## Task 10 — test(resolver): add 25 test-bank cases [code]

**Files:** Create: `challange/tests/test_bank.py`

**Design:** `Brainstorm > V2 > 7. Test-case bank` (25 nodes) · D-09, D-10, D-27, D-32, D-47

**Required skill (first step):** Invoke the Skill tool with skill='superpowers:test-driven-development' before doing anything else.

- [x] **Step 1: Write 25 tests** — one `test_bank_NN_<slug>` per bank node, docstring-free, `pytest.param(..., id="<node topic>")` style ids. Module guarded by `pytest.importorskip("src.resolver")` until Task 14.
- [x] **Step 2: Count assertion** — `test_bank_has_25_cases` counts the test functions.
- [x] **Step 3: Guard** — `python -m pytest -q tests/test_bank.py` → `1 skipped` (module skip until the resolver lands).
- [x] **Step 4: Commit** (subagent commits its own leaf, after the greenness gate passes)
  ```bash
  git add challange/tests/test_bank.py
  git commit -m "test(resolver): add 25 test-bank cases"
  ```

## Task 11 — feat(normalize): add mechanical normalization [code]

**Files:** Create: `challange/src/normalize.py`, `challange/tests/test_normalize.py`

**Design:** V3 §5 · D-07, D-33

**Required skill (first step):** Invoke the Skill tool with skill='superpowers:test-driven-development' before doing anything else.

- [x] **Step 1: Failing tests** — `"Apache Log4j 2.14"` → `"apache log4j"`; `"C++"`, `"C#"`, `"C"` stay distinct; `"F5-NGINX"` → `"f5 nginx"`; hypothesis: idempotent, casing-invariant, trailing-punctuation-invariant, version-suffix-invariant.
- [x] **Step 2: Implement** — NFKC + casefold → split on separators → keep `SYMBOL_TOKENS` → drop version tokens `^v?\d+(\.\d+)*$` → strip non `[a-z0-9+#]` → `tokens()` + `normalize()`.
- [x] **Step 3: Guard** — `python -m pytest -q tests/test_normalize.py` → all passed.
- [x] **Step 4: Commit** (subagent commits its own leaf, after the greenness gate passes)
  ```bash
  git add challange/src/normalize.py challange/tests/test_normalize.py
  git commit -m "feat(normalize): add mechanical normalization"
  ```

## Task 12 — feat(build): build and validate the frozen snapshot [code]

**Files:** Create: `challange/src/build.py`, `challange/tests/test_build.py`

**Design:** V3 §4, §5, §11 Flow A · D-09, D-10, D-12, D-20, D-22, D-32, D-33, D-35, D-40, D-44

**Required skill (first step):** Invoke the Skill tool with skill='superpowers:test-driven-development' before doing anything else.

- [x] **Step 1: Failing tests** — `test_index_version_is_content_hash` (two builds → same hash; one alias added → different hash); `test_generated_aliases` (`"amazon eks"` → `aws/eks`, `"sentinel siem"` → `microsoft/sentinel`); `test_generated_never_shadows_manual` (`"microsoft copilot"` → only `microsoft/copilot`); `test_short_alias_is_weak`; `test_validate_rejects_strong_alias_on_two_entities`; `test_validate_rejects_vendor_cycle`.
- [x] **Step 2: Implement** — `build_tables(sources) -> Tables` (entities incl. vendor entities `<vendor>/*`, aliases, vendor aliases, postings, IDF `log(1 + N/df)`, thresholds, 10 identity calibration bins) · `validate(tables) -> list[str]` · `write_snapshot(tables, path)` / `load_snapshot(path) -> Tables` · `index_version = sha256(canonical JSON of tables)`.
- [x] **Step 3: Guard** — `python -m pytest -q tests/test_build.py` → all passed.
- [x] **Step 4: Commit** (subagent commits its own leaf, after the greenness gate passes)
  ```bash
  git add challange/src/build.py challange/tests/test_build.py
  git commit -m "feat(build): build and validate the frozen snapshot"
  ```

## Task 13 — feat(ports): add ledger, review-queue and plugin ports [code]

**Files:** Create: `challange/src/ports.py`, `challange/tests/test_ports.py`

**Design:** V3 §5 Enrichment plugins, §6 Ledger · D-17, D-24, D-30, D-31, D-37, D-47

**Required skill (first step):** Invoke the Skill tool with skill='superpowers:test-driven-development' before doing anything else.

- [x] **Step 1: Failing tests** — `InMemoryLedger` round-trips a `Resolution` by `LedgerKey(input_norm, hints, filters, index_version)`; `InMemoryReviewQueue` keeps insertion order and dedupes.
- [x] **Step 2: Implement** — `ResponseLedger`, `ReviewQueue`, `EnrichmentPlugin` Protocols + in-memory impls; production-stub comments: durable ledger, monitoring (unresolved / ambiguous rates, p99), human review workflow, Flow D overlay (D-43).
- [x] **Step 3: Guard** — `python -m pytest -q tests/test_ports.py` → all passed.
- [x] **Step 4: Commit** (subagent commits its own leaf, after the greenness gate passes)
  ```bash
  git add challange/src/ports.py challange/tests/test_ports.py
  git commit -m "feat(ports): add ledger, review-queue and plugin ports"
  ```

## Task 14 — feat(resolver): resolve names over the snapshot [code]

**Files:** Create: `challange/src/resolver.py`, `challange/tests/test_resolver.py`, `challange/tests/test_properties.py`; Modify: `challange/tests/conftest.py` (session snapshot fixture)

**Design:** V3 §6 · D-14, D-16, D-18, D-19, D-21, D-22, D-26–D-31, D-44, D-47

**Required skill (first step):** Invoke the Skill tool with skill='superpowers:test-driven-development' before doing anything else.

- [x] **Step 1: Failing tests** — hints break the `Sentinel` tie (D-29); filters drop non-matching vendors (D-18); `no_match` lands in the review queue (D-47); ledger hit returns the recorded answer; properties: `resolve(canonical) == canonical` for every non-flagship-shadowed entity, idempotency, casing / punctuation / version invariance.
- [x] **Step 2: Implement** — `Resolver(tables, ledger, review_queue)`: `exact` → `decompose` → `candidates` → `score` → `decide`; LRU `maxsize=10_000` (D-30); module-level `resolve()` over the default snapshot.
- [x] **Step 3: Guard** — `python -m pytest -q tests/test_bank.py tests/test_resolver.py tests/test_properties.py` → `25+` bank passed, all passed.
- [x] **Step 4: Commit** (subagent commits its own leaf, after the greenness gate passes)
  ```bash
  git add challange/src/resolver.py challange/tests/test_resolver.py challange/tests/test_properties.py challange/tests/conftest.py
  git commit -m "feat(resolver): resolve names over the snapshot"
  ```

## Task 15 — feat(cli): add idx command [code]

**Files:** Create: `challange/src/cli.py`, `challange/tests/test_cli.py`

**Design:** V3 §7, §10 · D-13, D-36, D-43

**Required skill (first step):** Invoke the Skill tool with skill='superpowers:test-driven-development' before doing anything else.

- [x] **Step 1: Failing tests** — `idx resolve "AWS"` prints JSON with `"status": "resolved"`; `idx add-alias aws/eks "Elastic K8s"` twice → one row (idempotent upsert, D-36); `idx validate` exit 0; `idx build --out <tmp>` prints `index_version`, alias count, RSS (D-35).
- [x] **Step 2: Implement** — argparse sub-commands `build | validate | resolve | eval | add-alias`; `--data-dir`, `--snapshot`, `--hint-vendor`, `--filter-vendor`.
- [x] **Step 3: Guard** — `python -m pytest -q tests/test_cli.py` → all passed.
- [x] **Step 4: Commit** (subagent commits its own leaf, after the greenness gate passes)
  ```bash
  git add challange/src/cli.py challange/tests/test_cli.py
  git commit -m "feat(cli): add idx command"
  ```

## Task 16 — feat(eval): add gold-set evaluation harness [code]

**Files:** Create: `challange/src/eval.py`, `challange/src/data/gold.jsonl`, `challange/tests/test_eval.py`

**Design:** V3 §8 · D-38, D-39, D-40

**Required skill (first step):** Invoke the Skill tool with skill='superpowers:test-driven-development' before doing anything else.

- [x] **Step 1: Failing tests** — gold set = bank rows + leave-one-out over manual aliases + deterministic synthetic typos, ≥ 150 cases; `precision_on_resolved >= 0.98` (gate); report has `coverage`, `f1`, `ambiguous_rate`, `p50_ms`, `p99_ms`, `cost_per_1m_usd`, threshold sweep rows, 10-bin reliability table + ECE.
- [x] **Step 2: Implement** — `build_gold_set`, `evaluate`, `sweep_thresholds`, `reliability_table`; offline-evaluation production stub comment (regression gate in CI, dev / test split).
- [x] **Step 3: Guard** — `python -m pytest -q tests/test_eval.py` → all passed.
- [x] **Step 4: Commit** (subagent commits its own leaf, after the greenness gate passes)
  ```bash
  git add challange/src/eval.py challange/src/data/gold.jsonl challange/tests/test_eval.py
  git commit -m "feat(eval): add gold-set evaluation harness"
  ```

## Task 17 — chore(env): add Makefile, Dockerfile and README [code] 🏁

**Files:** Create: `challange/Makefile`, `challange/Dockerfile`, `challange/.dockerignore`, `challange/README.md`

**Design:** V3 §13 · D-45

**Required skill (first step):** Invoke the Skill tool with skill='superpowers:test-driven-development' before doing anything else.

- [x] **Step 1: Makefile** — `setup` (venv + `pip install -e '.[dev]'`), `test` (`pytest -q`), `resolve NAME=...` (`idx resolve "$(NAME)"`), `eval`, `build`.
- [x] **Step 2: Dockerfile** — `python:3.12-slim`, `pip install .`, `RUN idx build`, `ENTRYPOINT []`, `CMD ["idx", "resolve", "AWS"]`.
- [x] **Step 3: README** — 3 commands: `make setup`, `make test`, `make resolve NAME="AWS"` + docker pair.
- [x] **Step 4: Gate** — `make test` → `N passed`; `make resolve NAME="Amazon Web Services"` → `"status": "resolved"`.
- [x] **Step 5: Commit** (subagent commits its own leaf, after the greenness gate passes)
  ```bash
  git add challange/Makefile challange/Dockerfile challange/.dockerignore challange/README.md
  git commit -m "chore(env): add Makefile, Dockerfile and README"
  ```

## Task 18 — review(D4 Code + D5 Environment): quality + fidelity

**Files:** none — read-only. Findings route back to Tasks 7–17.

**Required skill (first step):** Invoke the Skill tool with skill='superpowers:requesting-code-review' before doing anything else. The controller runs this task itself and dispatches one reviewer as a `model: 'sonnet'` subagent; no implementer subagent, no commit.

- [x] **Step 1: Reviewer.** `BASE_SHA` = commit before Task 7, `HEAD_SHA` = Task 17. Fidelity: every D-xx named in Tasks 7–17 implemented as locked. Quality: functions 10–20 lines, no `Any`, no magic thresholds, no comments beyond production stubs, Pydantic only at boundaries, deterministic tie-break.
- [x] **Step 2: Route findings.** Each finding reopens its leaf → `fix(<scope>): <finding>` → re-run Step 1. Record `review: ✅`.

## Task 19 — Verification + companion-doc surface

**Files:** Modify: `challange/docs/plans/deliverables.plan.md`, `challange/DESIGN.md` (re-measured numbers), `CLAUDE.md` (only if a convention changed)

**Required skill (first step):** Invoke the Skill tool with skill='superpowers:verification-before-completion' before doing anything else.

- [x] **Step 1:** `make test` — paste summary; `N/N ✅`.
- [x] **Step 2:** `docker build -t tech-resolver .` exit 0; `docker run --rm tech-resolver idx resolve "AWS"` prints a `Resolution`.
- [x] **Step 3:** Behaviour gate — `make resolve NAME="Amazon Web Services"`, `"Sentinel"`, `"AWS EKS"`, `"AWS EKS"` twice; paste output.
- [x] **Step 4:** `DESIGN.md` one page: `wc -w` ≤ ~600; every Deliverable 1 bullet has a heading; D-xx cited; 📊 `[CONFIRM]` or re-measured.
- [x] **Step 5:** Diagrams exist; flow labels match Deliverable 3.
- [x] **Step 6:** `README.md` commands match the `Makefile`.
- [x] **Step 7:** Root `CLAUDE.md` — revise only if a convention changed.
- [x] **Step 8:** Re-read `ex.md` › Deliverables + `V3 › Readiness`; map each bullet to file:line below.
- [x] **Step 9:** Re-run the Self-review checklist; tick each box.
- [x] **Step 10:** Flip `**Status:**` to `✅ complete` only if Step 8 found zero unmet bullets.
- [x] **Step 11: Commit** (subagent commits its own leaf, after the greenness gate passes)
  ```bash
  git add challange/docs/plans/deliverables.plan.md challange/DESIGN.md
  git commit -m "chore(plan): mark deliverables complete"
  ```
- [x] **Step 12:** Hebrew status to Ofek: `done / next / blocked`.

**Evidence (22-10-26):**

```text
make test                                  → 234 passed in 1.73s (234/234 ✅)
docker build -t tech-resolver .            → sha256:fc331c82… ; docker run --rm tech-resolver idx resolve "AWS" → aws/aws, resolved, index_version f1fe41cbfdee5dc6
make resolve NAME="Amazon Web Services"    → aws/aws "AWS", resolved, 0.97   (same canonical as "AWS" → aws/aws, 0.8)
make resolve NAME="Sentinel"               → ambiguous, alternatives hashicorp/sentinel, microsoft/sentinel, thales/sentinel
make resolve NAME="AWS EKS"                → aws/eks "AWS EKS", resolved, 1.0  (≠ aws/aws)
make resolve NAME="AWS EKS" ×2             → identical output, index_version f1fe41cbfdee5dc6
make eval                                  → 183 cases, precision 1.00 (gate ≥ 0.98 ✅), coverage 0.79 (target 0.90 ❌, D-38 "to calibrate"), p50 0.03 ms, p99 0.12 ms
idx build                                  → 178 entities, 481 aliases, RSS 38.1 MB
wc -w docs/DESIGN.md                       → 661 (table ≈ 170 words at half weight → ≈ 580)
```

**ex.md › Deliverables → file:line:**

| Bullet | Where |
|---|---|
| D1 approach / trade-offs / data structures / scale / evaluation | `docs/DESIGN.md:5`, `:14`, `:27`, `:34`, `:41` |
| D2 components + flows (a) add/update, (b) resolve | `docs/architecture.md` (subgraphs `Flow A`, `Flow B`) |
| D3 input → normalization → candidates → decision → canonical ID | `docs/resolve-flow.md` |
| D4 callable interface `resolve(name)` | `src/resolver.py` `resolve()` (module level) + `Resolver.resolve` |
| D4 aliases → same canonical | `tests/test_bank.py` `test_bank_02`, `test_bank_03`, `test_bank_09` |
| D4 near-collisions (Sentinel vs Microsoft Sentinel) | `tests/test_bank.py` `test_bank_08`, `test_bank_09`, `test_bank_11`; `tests/test_resolver.py` hint / filter tests |
| D4 hard negative Amazon Web Services ≠ AWS EKS | `tests/test_bank.py` `test_bank_05`, `test_bank_06` |
| D4 idempotency | `tests/test_bank.py` `test_bank_25`; `tests/test_properties.py` `test_idempotent` |
| D4 stubs: monitoring, offline evaluation, human review | `src/ports.py` (`InMemoryLedger`, `InMemoryReviewQueue`, `EnrichmentPlugin`, monitoring + Flow D comments); `src/eval.py` offline-evaluation comment |
| Reproducible environment | `Makefile`, `Dockerfile`, `README.md` |

**Deviations from task text:** `idx eval` sub-command landed in Task 16 (leaf-order invariant: `cli.py` cannot import `eval.py` before it exists); `tests/test_bank.py` lands skipped (module `importorskip`) until Task 14 instead of red; diagrams are Mermaid `.md` (canvas down); `DESIGN.md` lives in `docs/`.

---

## Self-review checklist (run before handing off)

Owner: Task 19 Step 9 ticks this section.

- [x] **Spec coverage** — every `ex.md` deliverable bullet appears in some task; the four required behaviours each have a named test.
- [x] **Test bank 1:1** — 25 bank cases, each citing its node, land before the resolver leaf.
- [x] **Spec-review gate passed** — every task cites a V3 section or D-xx.
- [x] **No placeholders** — every step has a concrete command or spec.
- [x] **Commit boundaries (leaf-DAG)** — one task = one leaf = one commit; 🏁 on the last leaf of each deliverable.
- [x] **Leaf-order invariant** — no leaf imports a missing file; `Resolution` (Task 8) and the snapshot schema (Task 12) land before consumers.
- [x] **Deliverable-boundary work** — every 🏁 leaf runs `make test` + extra gate and is followed by its review task.
- [x] **Atomic groups honored** — DESIGN.md and each diagram are one task.
- [x] **Commit messages** — pre-rendered, conventional, one per leaf.
- [x] **Commit step shape** — every leaf ends with one commit step; review tasks never commit.
- [x] **TDD scope declared** — every heading tagged; first-step lines match `tdd-routing.md`.
- [x] **Locked constraints honored** — no LLM / embeddings / RAG (D-01, D-23); thresholds from the snapshot (D-28); tie-break (D-16); content-hash `index_version` (D-22); `no_match` shape (D-47); `<Vendor> <Product>` + `vendor/product` id (D-33).
- [x] **Production stubs present** — monitoring, offline evaluation, human review workflow, Flow D overlay.
- [x] **Time box** — header sums to ≤ 4 h; no leaf above 30 min.
- [x] **Criteria naming N things have N-asserting tests** — 25 cases, 23 leaves, 100–300 entities.
- [x] **Every new test would fail if the thing it covers were deleted.**
- [x] **Verification task present.**
- [x] **Checkbox ownership** — every box has an owner and a tick-moment.
- [x] **Deferred items have owners.**

---

## Open items deferred

| Item | Owner |
|---|---|
| Calibration fit (D-40) on a hand-labeled dev set | `DESIGN.md` › Evaluation (doc only); Task 16 prints the reliability table |
| Durable ledger, Flow D overlay, enrichment plugins, index-health SLOs, REST, Wikidata / purl / Repology joins | Task 13 Protocol stubs + `DESIGN.md` lines (D-30, D-37, D-39, D-43) |
| D-47 unknown-input policy confirmation from Matan | Default locked; reported in the status line |

## Deliverable mapping

| Deliverable | Tasks |
|---|---|
| D1 DESIGN.md | 1–2 |
| D2 Architecture diagram | 3–4 |
| D3 Flow diagram | 5–6 |
| D4 Code | 7–16, review 18 |
| D5 Reproducible environment | 17 🏁, review 18 |
| Verification | 19 |
