# Technology Entity Disambiguation — Design

Diagrams: [architecture](architecture.md) · [resolve flow](resolve-flow.md). D-xx = locked decision ids.

## Approach

Dictionary-first, deterministic, closed world (D-01, D-23, D-47).
An offline build turns reviewed source files into one immutable snapshot; `resolve(name, *, hints, filters)` only reads it.
Runtime normalization is mechanical; every semantic variant ships as a reviewed alias (D-07, D-08).
No LLM or embeddings at request time: hard negatives (CrowdStrike Falcon vs SentinelOne) are semantically close, and the cost target is ≤ $1 per 1M (D-01, D-23).

Output: `Resolution{id, canonical_name, vendor, category, confidence, status, alternatives, index_version}`.

## Key decisions & trade-offs

| Topic | Decision | Trade-off |
|---|---|---|
| Precision vs recall | Precision first; initial base by match type canonical 1.0 > manual 0.97 > generated 0.9 > weak-unique 0.8 > fuzzy = score (D-14, D-27) | Some true variants return `ambiguous` / `no_match` |
| Decision rule | initial: `resolved` iff `s1 ≥ T_high (0.75)` and `margin ≥ M (0.15)`; `ambiguous` iff `s1 ≥ T_low (0.5)`; else `no_match` (D-22, D-28) | Threshold change = new version |
| Ambiguity | Product-only and ≤ 3-char aliases are weak; a weak alias on > 1 entity returns `ambiguous` + alternatives (`Sentinel`); a vendor in the input is a hint (`Microsoft Sentinel`) (D-09, D-19, D-29) | Callers handle a third status |
| Hierarchy | Canonical vendor = operating brand, `parent_vendor_id` is metadata; `Amazon ≠ AWS`, `AWS ≠ AWS EKS` (D-10, D-11, D-32) | Build emits parent × product aliases; no runtime tree walk (D-44) |
| Typos | Trigram candidates + Levenshtein ≤ 2; ≤ 3 chars exact only (D-26) | Misses heavier misspellings |
| Unknowns | `no_match`, confidence 0, queued for review; runtime never mints ids (D-47, assumption [CONFIRM]) | Coverage grows only via review |
| Update strategy | Source files in git, PR = review, idempotent upserts with provenance; build → validate → eval gate → atomic snapshot swap (D-12, D-13, D-36) | A rebuild per change |
| Idempotency | `index_version` = content hash; ledger key = `(input, hints, filters, index_version)`; tie-break `(score desc, entity_id asc)` (D-16, D-22, D-31) | Ledger grows with traffic |

## Data structures

- **Canonical entity:** id `vendor/product` (ascii slug, CPE WFN, immutable); display `<Vendor> <Product>`, vendor omitted when the product starts with it, symbols kept (`C++`, `.NET`) (D-33). Vendors are entities too (`microsoft/*`, category `vendor`).
- **Sources (git):** `categories.yaml` (23 leaves), `vendors.csv` (parent, flagship), `entities.jsonl`, `aliases.csv` with provenance (D-34, D-42).
- **Snapshot (one SQLite file):** entities; `alias_norm → [(entity_id, strength)]`; `vendor_alias → vendor_id`; inverted index `token → aliases`; IDF; thresholds; calibration bins (D-20, D-35).
- **Score:** IDF-weighted token-set Jaccard; the union counts alias tokens missing from the input (coverage penalty) (D-21).

## Scale to 100k+

- **Latency:** exact alias O(1); candidates from postings of rare tokens, top-K = 20 scored (D-28); in-process p99 target < 5 ms (D-39).
- **Memory:** ~1M aliases fit one SQLite file; in-memory exact-alias dict ≈ 150–250 MB [CONFIRM]; beyond that, SQLite-backed lookups (D-35).
- **Maintainability:** per-vendor files + CODEOWNERS, validator in CI, replay diff per version, traffic-weighted health (D-25, D-36, D-42).
- **Build:** offline, incremental; enrichment plugins only propose changesets (D-24, D-37).

## Evaluation infrastructure

- **Gold set:** 25 hand cases + leave-one-out over aliases + synthetic typos in code; 300–500 hand-labeled in production (D-38).
- **Metrics (`make eval`):** precision on resolved (gate ≥ 0.98), coverage (target ≥ 0.90), F1, ambiguous rate, p50 / p99 latency, cost per 1M, threshold sweep, 10-bin reliability table + ECE (D-38, D-40).
- **Measured (seed, 22-10-26):** 178 entities, 481 aliases, 183 cases: precision 1.00, coverage 0.79 (leave-one-out misses fall to `no_match`), p50 0.03 ms, p99 0.12 ms.
- **Calibration:** bins frozen in the snapshot; fit on the hand-labeled dev set, since leave-one-out inflates precision (D-40).
- **Production:** regression gate in CI; health SLOs unresolved < 5 %, ambiguous < 3 %, tier-1 precision ≥ 99 % [CONFIRM] (D-25, D-39).
- **Stubbed:** durable ledger, review queue, monitoring, plugins, real-time overlay (D-30, D-43).
