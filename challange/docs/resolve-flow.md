# Resolve flow

Input string → normalization → exact on the input as typed → synonym rewrite → exact + fuzzy on the rewritten text → decision → canonical ID (V3 §6, V4).
Thresholds T_high 0.75, T_low 0.5, M 0.15, K 20 and the hint bonus +0.15 are read from the snapshot (D-28, D-29).

```mermaid
flowchart TD
    IN["Input string<br/>+ hints (soft) + filters (hard) (D-18)"] --> NORM["Normalize (D-07, D-33)<br/>NFKC, casefold, split, keep C++ / C# / .NET,<br/>drop dotted or v-prefixed versions, keep bare integers"]
    NORM --> CACHE{"LRU / ledger hit?<br/>key = input, hints, filters, index_version (D-30, D-31)"}
    CACHE -->|yes| OUT
    CACHE -->|no| EXACT{"A · input as typed<br/>exact alias → joined words → without numbers (products only)"}
    EXACT -->|hit| BASE["Base by match type (D-27)<br/>canonical 1.0 · manual 0.97 · generated 0.9 · weak 0.8<br/>+ hint bonus for ranking (D-29)"]
    EXACT -->|miss| SYN["B · SynonymRewrite (D-49)<br/>unknown words → concept: k8 → kubernetes"]
    SYN --> EXACT2{"exact steps again on rewritten text<br/>concept aliases live here (ConceptCombos)"}
    EXACT2 -->|hit| BASE
    EXACT2 -->|miss| DEC["Decompose: vendor longest-prefix<br/>vendor = inferred hint, residue must match (D-19, D-44)"]
    DEC --> CAND["Candidate retrieval (D-20, D-26)<br/>postings of input tokens;<br/>typo: trigram vocab + Levenshtein ≤ 2, tokens > 3 chars"]
    CAND --> SCORE["Score (D-21)<br/>IDF-weighted token-set Jaccard<br/>+ coverage penalty; top-K + hint bonus"]
    BASE --> DECIDE
    SCORE --> DECIDE{"C · Decide on (raw s1, margin) (D-22, D-48)<br/>bonus ranks and widens margin only<br/>tie-break: score desc, entity_id asc (D-16)"}
    DECIDE -->|"raw s1 ≥ T_high and margin ≥ M"| RESOLVED["resolved<br/>canonical ID + confidence"]
    DECIDE -->|"s1 ≥ T_low"| AMB["ambiguous<br/>alternatives, conf = s_i / Σ s"]
    DECIDE -->|"else"| NOM["no_match<br/>canonical_name = null, confidence 0<br/>→ review queue (D-47)"]
    RESOLVED --> REC["Record in ledger + LRU"]
    AMB --> REC
    NOM --> REC
    REC --> OUT["Resolution + index_version"]
```
