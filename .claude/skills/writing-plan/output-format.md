# writing-plan — Output format and File Map

> Detail for [SKILL.md](SKILL.md). On conflict, SKILL.md §Hard rules wins.

## Output contract

A single Markdown file at `challange/docs/plans/<slug>.plan.md` (for the whole challenge: `deliverables.plan.md`).

The file has exactly these sections, in this order:

```markdown
# <slug> — <descriptive title> (Implementation Plan)
<mandatory header block>
---
## File Map
---
### D1 DESIGN.md
## Task 1 — … [docs] 🏁
## Task 2 — review(D1 DESIGN.md): quality + fidelity
### D2 Architecture diagram
…
### D4 Code
## Task k — … [code]
## Task m — … [code] 🏁
## Task m+1 — review(D4 Code): quality + fidelity
…
## Task N — Verification + companion-doc surface
---
## Self-review checklist (run before handing off)
---
## Open items deferred (optional)
## Deliverable mapping (required)
```

No additional top-level sections. No prose-only introduction beyond the header block.

---

## File Map section

Two explicit lists plus a test-commands block:

- **`**Create:**`** — every file any task will create, under `challange/`: `DESIGN.md`, `docs/architecture.excalidraw|png`, `docs/resolve-flow.excalidraw|png`, `src/data/{categories.yaml,vendors.csv,entities.jsonl,aliases.csv}`, `src/{constants,models,normalize,build,resolver,ports,cli,eval}.py`, `tests/*.py`, `Makefile`, `Dockerfile`, `README.md`, `pyproject.toml` or `requirements.txt`. No glob, no "and similar".
- **`**Modify:**`** — every file any task will modify. **Always include the plan file itself** — the controller ticks checkboxes as leaves complete and the final verification task commits them.
- **`**Test commands:**`** — code-fenced bash from [`../_shared/greenness-ladder.md`](../_shared/greenness-ladder.md):

```bash
python -m pytest -q tests/<file>            # guard — every leaf
make test                                    # verify — task done / 🏁
make test && docker build -t tech-resolver . # sweep — final verification
```

No placeholder paths. If a name depends on an undecided value, pick it now and commit to it.
