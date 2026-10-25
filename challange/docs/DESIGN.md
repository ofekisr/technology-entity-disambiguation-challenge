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
| Decision rule | `resolved` iff raw `s1 ≥ T_high (0.75)` and `margin ≥ M (0.15)`; `ambiguous` iff `s1 ≥ T_low (0.5)`; else `no_match`. Hints (caller or vendor found in the input) add a bonus that ranks and widens the margin, never lifts the raw score (D-22, D-28, D-48) | "Splunk Enterprise Security" → `ambiguous`, not Splunk Enterprise |
| Ambiguity | Product-only and ≤ 3-char aliases are weak; a weak alias on > 1 entity returns `ambiguous` + alternatives (`Sentinel`). `ambiguous` = candidates above `T_low`, none passes the rule; an alternative's confidence is its share of the shown evidence, so one alternative shows 1.0 (D-09, D-19, D-29) | Callers handle a third status |
| Normalization | Dotted or `v`-prefixed versions dropped (`2.14.1`, `v7`); bare integers kept. On an exact miss: retry with adjacent words joined (`Sentinel One`), then without integers for products only, capped at weak (`Windows 10`; `Microsoft 365` ≠ Microsoft) | Joined → split (`RedHat`) not handled |
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
- **Code shape:** the build runs a list of `AliasSource` strategies (canonical names, vendor × product, category × product, vendor names, curated rows, concept combos).
The resolver runs `SynonymRewrite` around a `FirstHit` chain of `Matcher` strategies (exact, joined words, without numbers, fuzzy), then one `Decider`.
A new source or matcher is one class; `Resolver(matcher=...)` and `build_tables(alias_sources=...)` accept custom chains.

## Semantic equivalence

Free text says `Amazon managed k8` and means `aws/eks`; aliases alone don't cover every phrasing.
Meaning is paid for once per product at build time, not once per request:

- **Concept layer (V4):** `concepts.csv` (term → concept, `k8s → kubernetes`) and `entity_concepts.csv` (`aws/eks → kubernetes, managed`, with weight and provenance).
- **Index:** one more `AliasSource` turns concept edges into generated aliases, `<vendor> × <concept phrase>` (`amazon managed kubernetes → aws/eks`), the D-44 pattern; concept-only phrases hit several products and return `ambiguous`.
- **Resolver:** one more `Matcher` rewrites synonyms before the exact lookup (`k8 → kubernetes`); same snapshot, same determinism (amends D-07).
- **Sources:** curated synonyms (Wikidata, StackOverflow tag synonyms), product docs (TF-IDF against same-vendor siblings), reviewed LLM proposals (D-24, D-37); package registries feed hard negatives only.
- **Not at runtime:** embeddings and paid APIs stay offline as proposal sources; they score same-vendor siblings (Falcon vs Falcon, Sentinel × 3) as near-identical, where a confident wrong answer costs most (D-01, D-23).

Status: built 26-10-26 with 130 concepts, 29 synonyms and 203 seeded concept edges (`source=seed`, pending review); synonym rewrite skips any word the index already knows (D-49).
5 of 6 paraphrase gold cases resolve; `MS Teams` misses on the missing `MS` vendor alias, not on meaning.
Concept-only input (`managed kubernetes`) returns `ambiguous` (EKS, GKE).

## Scale to 100k+

- **Latency:** exact alias O(1); candidates from postings of rare tokens, top-K = 20 scored (D-28); in-process p99 target < 5 ms (D-39).
- **Memory:** ~1M aliases fit one SQLite file; in-memory exact-alias dict ≈ 150–250 MB [CONFIRM]; beyond that, SQLite-backed lookups (D-35).
- **Maintainability:** per-vendor files + CODEOWNERS, validator in CI, replay diff per version, traffic-weighted health (D-25, D-36, D-42).
- **Build:** offline, incremental; enrichment plugins only propose changesets (D-24, D-37).

## Evaluation infrastructure

- **Gold set:** 49 hand cases (incl. 6 paraphrase, 14 hard-negative) + leave-one-out over aliases + synthetic typos in code; 300–500 hand-labeled in production (D-38).
A test guards that no hard negative resolves to a wrong id.
- **Metrics (`make eval`):** precision on resolved (gate ≥ 0.98), coverage (target ≥ 0.90), F1, ambiguous rate, p50 / p99 latency, cost per 1M, threshold sweep, 10-bin reliability table + ECE (D-38, D-40).
The gate checks precision only; coverage is reported against its target, not gated.
- **Measured (seed + V4, 26-10-26):** 178 entities, 745 aliases, 195 cases: precision 1.00, coverage 0.78 (leave-one-out misses fall to `no_match` / `ambiguous`), p50 0.04 ms, p99 0.28 ms.
- **Calibration:** bins frozen in the snapshot; fit on the hand-labeled dev set, since leave-one-out inflates precision (D-40).
- **Production:** regression gate in CI; health SLOs unresolved < 5 %, ambiguous < 3 %, tier-1 precision ≥ 99 % [CONFIRM] (D-25, D-39).
- **Stubbed:** durable ledger, review queue, monitoring, plugins, real-time overlay (D-30, D-43).
