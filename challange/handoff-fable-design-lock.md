# Handoff: review Brainstorm V2 + Design V2, lock open decisions (22-10-26)

## Role and goal
You are reviewing the design of a home-assignment challenge for Ofek (senior engineer). The output is a **locked design**: every open decision has a chosen answer, so Ofek can write the 1-page design doc and the code the challenge asks for. You review and decide; Ofek approves. Do not write the design doc or code.

## Files (folder: /Users/ofeki/works/mars-security/challange/)
- `ex.md` (also `ex.pdf`): the challenge brief. **Read it first; it is the only source of requirements.**
- `ex.mmap`: Mind Elixir JSON mind map. Root `data.nodeData` has `Problem`, `Brainstorm` (`V2`, `V1`), `Design` (`V2 (22-10-26)`, `V1`). Nodes: `{topic, id, note?, children?, hyperLink?}`.
- Conventions (node `Brainstorm > V2 > Conventions`): ⭐ chosen · ❓ open · ✗ rejected · ↻ revised · ⏳ placeholder in Design (open) · 📄 paper/standard · 📊 measured · 💲 service · [CONFIRM] unverified.

To read the map, print it as an outline with notes (Python + json); it is ~1,200 nodes, so read the sections you need instead of dumping everything.

## Context
- Task: deterministic resolver from raw technology/product names in threat-intel reports to stable canonical (vendor + product) IDs, with confidence. Large universe (tens to hundreds of thousands). Required behaviour: aliases, near-collisions, hard negatives (AWS ≠ AWS EKS), unresolved inputs, the same output on every run.
- Answers from Matan, the company contact (`Brainstorm > V2 > 0. Inputs & constraints`): categories are ours and exist to shrink the search space; the input is one name; a TF-IDF corpus must be built or described; budget is about **$1 per 1M resolves**, so no LLM per request.
- Time budget: **3–4 hours** for the doc, the diagrams and the code. Prefer the simplest decision that passes the required tests; push the rest to "doc only".
- `Brainstorm > V2 > 8. Decisions log` holds D-01 to D-25 (locked). `Design > V2` holds only decided items plus ⏳ placeholders.
- Known caveat: the high-level flows A–D and the ledger (Design V2 › 2) were rebuilt from an earlier conversation after they went missing from the file. Check that they are coherent.

## Step 1: Review (findings only, no edits yet)
1. **Consistency:** every ⭐ and D-xx in Brainstorm V2 matches Design V2, and nothing in Design V2 is undecided without ⏳. Known suspects:
   - D-15 (Levenshtein ≤ 2) vs D-21 (trigram + Jaro-Winkler): one typo rule.
   - "Scale to 100k+" (~1M aliases ≈ 100MB fits) vs Q17 (up to 600MB in Python): this decides the runtime language and storage.
   - Q7 "weak but unique alias → lower confidence or ambiguous" vs the D-22 decision rule.
   - Design V2 › 10 (scope for 3–4h) may be too much: ledger + Flow D + plugins. Cut it to what passes the brief.
2. **Coverage against `ex.md`:** every deliverable and every required behaviour maps to a Design V2 node. List what is missing.
3. **Over-engineering:** anything that costs build time and does not help pass the brief → move it to "doc only".

## Step 2: Propose a decision for every open item
Sources of open items:
- `Brainstorm > V2 > 9. Parking lot > Open decisions (❓ copied from Q1–Q11)`
- `Brainstorm > V2 > 9. Parking lot > Open decisions from resolve deep-dive (22-10-26)`
- every ⏳ node in `Design > V2`
- anything you found in Step 1, including implementation language/runtime (Python 3.12 + FastAPI/pytest or Node 22 + TypeScript + Zod), which is not decided anywhere yet

"Proposal: …" notes already in the map are inputs, not answers; challenge them.

For each item give one row: `id · decision · why (1 line) · rejected alternative · evidence (map node / 📄 / 📊) · reversible? · risk`.
- Numeric items (T_high, T_low, M, K, hint bonus, LRU size, SLOs, gold-set size, precision target): give **initial defaults** and mark them `to calibrate on dev set`. Never leave them blank.
- The one item that needs Matan ("unknown input: unresolved vs provisional canonical"): lock a default plus a stated assumption for the doc, and draft the one-line question to Matan.
- Do not invent measurements. Anything unverified gets [CONFIRM].

**Stop and show Ofek the table**, grouped as: (a) obvious, so lock them all; (b) real trade-offs, which need his pick (use multiple-choice questions, at most 4); (c) needs Matan. Write nothing to the map until he approves.

## Step 3: Lock in the map (after approval)
1. Back up first: `cp ex.mmap ex.mmap.bak9-22-10-26`. Use the next free number if it exists.
2. Edit with a Python script that loads JSON, edits, and writes with `ensure_ascii=False, indent=2`. New node ids: `secrets.token_hex(8)`. Then validate that the JSON loads.
3. Append `D-26…` to `8. Decisions log` (format: `D-xx ⭐ decision`, note `Why: … Evidence: …`).
4. In the Parking lot, **do not delete**: prefix each resolved item with `↻ → D-xx`.
5. Create `Design > V3 (locked, DD-MM-YY)` at index 0: a copy of V2 with every ⏳ replaced by `🔒 decision (D-xx)`, plus a node `Doc map` that maps each section of the 1-page design doc required in `ex.md` to the V3 nodes that feed it. Leave V1 and V2 untouched.
6. Add a `Readiness` node under V3: deliverables from `ex.md` → ✅ covered / ❗ gap.

## Rules
- Map text in English, short topics, details in notes. Reply to Ofek in Hebrew. Code, ids and paths stay in English.
- No LLM, embeddings or RAG in the resolve path (D-01, D-23). LLM only as an optional offline enrichment plugin (D-24).
- Determinism: frozen snapshot, IDF, thresholds and calibration; tie-break (score desc, entity_id asc).
- If the app has `ex.mmap` open, tell Ofek to reload it before saving.

## Done when
Every open item is either 🔒 locked in Design V3 or explicitly waiting on Matan with a default; the Readiness node has no ❗ that blocks writing the doc; and Ofek has a 5-line summary of what changed.
