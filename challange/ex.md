# Technology Entity Disambiguation

## Background

When processing threat intel reports, we extract technology/product names mentioned in the text so we can match them against what each customer actually runs. The same technology often appears under many variants (e.g., "AWS", "Amazon Web Services", "AWS Cloud"), so we need entity disambiguation: resolving variants to a stable canonical identifier.

## The Challenge

Design and implement a deterministic entity disambiguation solution for technology names.

Given an arbitrary input string (a technology name extracted from a threat report), your system should return a stable canonical name such that:

- All variants of the same product resolve to the same canonical name
- Different products do not collapse into the same ID (or you have an explicit strategy for handling ambiguity/conflicts)
- The output is stable across runs and independent of non-deterministic components

Assume the canonical universe is large (tens of thousands).
## Scope

For this exercise, focus on:

- **Entity type:** technologies/products (clouds, EDRs, SIEMs, SaaS, libraries; your choice, but be consistent)
- **Canonical name format:** your design (e.g., "AWS EKS", "CrowdStrike Falcon", "Microsoft Sentinel"), including rules for casing, punctuation, and vendor/product ordering
- **Inputs:** raw strings only (no additional context from the report needed, unless you define an optional interface)
- **Knowledge source:** you may use a local dictionary/KB you construct, open datasets, or a small synthetic dataset you include in the repo
- **Out of scope:** building a full UI; production-scale data ingestion pipelines

## Deliverables

### 1. Design Document (max 1 page)

- Brief explanation of your approach
- Key design decisions and trade-offs (precision vs. recall, handling ambiguity, update strategy)
- Data structures used for canonical entities + alias/variant mapping
- Notes on how you'd scale to hundreds of thousands of canonicals (performance + maintainability)
- Evaluation Infrastructure: how performance is evaluated across various metrics (F1, Latency, Cost, etc.)

### 2. Architecture Diagram

- Major components
- Data flow for: (a) adding/updating canonical entities, (b) resolving an input string

### 3. Flow Diagram (1)

- Resolution flow: input string → normalization → candidate retrieval → decision → canonical ID

### 4. Code Implementation

- Any language
- Provide a callable interface, e.g.: `resolve(name: string) -> { canonical_name, confidence }`
- Include a minimal dataset + tests/examples demonstrating:
  - multiple aliases resolving to the same canonical
  - near-collisions (e.g., "Sentinel" vs "Microsoft Sentinel") and how you handle them
  - hard negatives: "Amazon Web Services" ≠ "AWS EKS"
  - idempotency
- Stub out production concerns (monitoring, offline evaluation, human review workflow) with comments describing what you'd add

### Reproducible Environment

- Simple run instructions (Docker, `make`, or a single script)

**Time expectation:** ~3–4 hours. Focus on the core resolver and a clear design rather than a full production system.
