# TDD routing (shared)

Route by task scope BEFORE dispatching any implementation subagent.
The verbatim first-step line is **subagent-facing** — the controller inlines it into the dispatched prompt.

## Scope → route → verbatim first-step line

| Scope | Route | Verbatim first-step line (inline into the prompt) |
|---|---|---|
| **code** (`src/`, `tests/`, `Makefile`, `Dockerfile`) | `superpowers:test-driven-development` | `Invoke the Skill tool with skill='superpowers:test-driven-development' before doing anything else.` |
| **docs** (`DESIGN.md`, `README.md`) | `write-markdown` + `elements-of-style:writing-clearly-and-concisely` | `Invoke the Skill tool with skill='write-markdown' before writing any prose. Budget: DESIGN.md is one page.` |
| **diagram** (`docs/architecture.*`, `docs/resolve-flow.*`) | `excalidraw-draw` (Mermaid fallback via `excalidraw`) | `Invoke the Skill tool with skill='excalidraw-draw' before drawing. If the canvas is unavailable, emit Mermaid into DESIGN.md and say so.` |
| **bug-fix** (failing test, wrong resolution, Docker break) | two-phase inspect → adapt | Phase A: `Invoke the Skill tool with skill='superpowers:systematic-debugging' before reproducing. Do not edit code.` |

## Code task-type → first-step line

| Task type | First-step line |
|---|---|
| Feature (normalize, build, resolver, cli, eval, ports) | `Invoke the Skill tool with skill='superpowers:test-driven-development' before doing anything else.` |
| Test-only (bank cases, hypothesis properties) | same as above |
| Boundary model (Pydantic for `entities.jsonl`, `aliases.csv`, `vendors.csv`, `categories.yaml`) | `Invoke the Skill tool with skill='dev-parse-validate' before doing anything else, then superpowers:test-driven-development.` |
| Smoke / final verification | `Invoke the Skill tool with skill='superpowers:verification-before-completion' before doing anything else.` |
| CLAUDE.md / README update | `Invoke the Skill tool with skill='claude-md-management:revise-claude-md' before doing anything else.` |

## Code conventions every code leaf inlines

- Functions 10–20 lines, no comments except the production-stub notes `ex.md` asks for (monitoring, offline evaluation, human review workflow).
- No `Any`. Full type hints. Pydantic models at file boundaries only.
- No magic numbers: thresholds (`T_high`, `T_low`, `M`, `K`, hint bonus) are read from the snapshot, never literals in `resolver.py`.
- Deterministic: tie-break `(score desc, entity_id asc)`; `index_version` = content hash.

## Bug-fix two-phase shape

- **Phase A (inspect, read-only, no commit):** reproduce → `superpowers:systematic-debugging` Phase 1 → classify the existing test `MISSING | WRONG | REDUNDANT | CORRECT-BUT-RED` → emit `{root_cause, test_classification, proposed_action, files_touched_in_phase_b}`.
- **Phase B (adapt, write-capable, branch on verdict):** `MISSING`/`CORRECT-BUT-RED` → normal TDD; `WRONG` → two commits (fix test, then fix prod); `REDUNDANT` → delete duplicate first.

Greenness gate for every scope: [`greenness-ladder.md`](greenness-ladder.md).
