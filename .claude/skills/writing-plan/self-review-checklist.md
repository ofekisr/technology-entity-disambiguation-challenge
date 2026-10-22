# writing-plan — Self-review checklist

> Detail for [SKILL.md](SKILL.md). On conflict, SKILL.md §Hard rules wins.

## Self-review checklist (mandatory final section)

**Checkbox ownership rule:** every `- [ ]` in the plan has an owner and a tick-moment — task step boxes are ticked by the controller as each leaf completes; this section is ticked by the final verification task's re-run.

Run this literally before declaring the plan ready and ship the section **unticked**:

- [ ] **Spec coverage** — every `ex.md` deliverable bullet (1–4 + reproducible environment) appears in some task; the four required behaviours each have a named test.
- [ ] **Test bank 1:1** — all 25 `7. Test-case bank` cases are parametrized tests, each citing its node; they land before the resolver leaf.
- [ ] **Spec-review gate passed** ([approval-and-amending.md](approval-and-amending.md)) — every task step cites a V3 section or D-xx; no bullet is silently unmet.
- [ ] **No placeholders** — every step has executable code or a concrete command. Allowed exception: `TODO(<reason>)` for a value that genuinely cannot be derived (e.g. a 📊 number awaiting re-measure).
- [ ] **Commit boundaries (leaf-DAG)** — one task = one leaf = one commit. Code leaves follow constants → models → data → test bank → normalize → build → resolver → ports → cli → eval → env last. The last leaf of every deliverable carries 🏁.
- [ ] **Leaf-order invariant** — no leaf imports a file that doesn't exist yet; `Resolution` and the snapshot schema land before any consumer.
- [ ] **Deliverable-boundary work** — every 🏁 leaf runs `make test` + its extra gate and is immediately followed by its review task; non-🏁 leaves run only `guard`.
- [ ] **Atomic groups honored** — DESIGN.md and each diagram are one task marked 🏁; not split.
- [ ] **Commit messages** — pre-rendered, conventional, one per leaf.
- [ ] **Commit step shape** — every leaf ends with one commit step labeled `(subagent commits its own leaf, after the greenness gate passes)`; review tasks end with a verdict and never commit.
- [ ] **TDD scope declared** — header item 10; every task heading carries its `[code|docs|diagram]` tag and its first-step line matches [`../_shared/tdd-routing.md`](../_shared/tdd-routing.md).
- [ ] **Locked constraints honored** — no LLM / embeddings / RAG in the resolve path (D-01, D-23); thresholds from the snapshot (D-28); tie-break (D-16); `index_version` = content hash (D-22); `no_match` shape (D-47); canonical `<Vendor> <Product>` + `vendor/product` id (D-33).
- [ ] **Production stubs present** — monitoring, offline evaluation, human review workflow, Flow D overlay each have a Protocol stub or comment leaf.
- [ ] **Time box** — header item 11 sums to ≤ 4 h; no leaf is budgeted above 30 min.
- [ ] **Criteria naming N things have N-asserting tests** — "25 cases", "23 category leaves", "100–300 entities" are asserted as counts, never one example.
- [ ] **Every new test would fail if the thing it covers were deleted.**
- [ ] **Verification task present** — final task uses `superpowers:verification-before-completion` and covers `make test`, `docker build`, the four CLI behaviours, DESIGN.md one page, README, `ex.md` re-read, Readiness, status flip.
- [ ] **Checkbox ownership** — every `- [ ]` has an owner and a tick-moment.
- [ ] **Deferred items have owners** — every "Open items deferred" entry names the task or the "doc only" line that owns it.

If any check fails, repair the plan; do not declare ready.
