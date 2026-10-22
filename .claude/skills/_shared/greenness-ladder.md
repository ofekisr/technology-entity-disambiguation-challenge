# Greenness ladder (shared)

Which command proves a change safe. Run the cheapest tier that proves your change.
All commands run from `challange/` (where the `Makefile` lives).

## The ladder

| Tier | Command | Cost | Run it | Proves |
|---|---|---|---|---|
| **guard** | `python -m pytest -q tests/<file>` (the test file the leaf touches) | seconds | after EVERY edit | the leaf's own red → green |
| **verify** | `make test` | < 1 min | before declaring a task / leaf done | the full suite (25 bank cases + leave-one-out + typos + hypothesis properties) |
| **sweep** | `make test && docker build -t tech-resolver .` | 1–3 min | once per 🏁 deliverable leaf, and in the final verification task | suite + reproducible environment |

## Extra gates per deliverable kind

| Deliverable | Gate |
|---|---|
| `DESIGN.md` | fits one page: `wc -w DESIGN.md` ≤ ~600 words, and every `ex.md` › Deliverable 1 bullet has a heading |
| `docs/architecture.*`, `docs/resolve-flow.*` | file exists; flow steps match `ex.md` › Deliverable 3 (`normalization → candidate retrieval → decision → canonical ID`) |
| `README.md` | the 3 documented commands run from a clean clone (`make setup`, `make test`, `make resolve NAME="AWS"`) |
| CLI | `make resolve NAME="Amazon Web Services"` prints a `Resolution` with `status: resolved` |

## Mapping to the leaf lifecycle

- **Non-🏁 leaf** → gate = **guard**. Subagent commits after `guard` is green.
- **Task-done / declaring a leaf complete** → **verify**.
- **🏁 deliverable-boundary leaf** → **verify** + the deliverable's extra gate, then the plan's review task.
- **Final verification task** → **sweep** once, plus every extra gate above.

## Evidence shape

Paste the command and its tail. Required line for `verify`: pytest's summary, e.g. `41 passed in 2.3s`.
Report as `N/N ✅` in status lines. "Should pass" is not evidence.

## Stale patterns to NOT use

- ❌ Running `docker build` on every red → green iteration — `sweep` is a boundary gate.
- ❌ Calling `pytest` without `-q` in subagent output — the full dots wall floods the controller.
- ❌ Hand-scoping `make test` to "only the changed file" at a 🏁 leaf — the boundary runs the whole suite on purpose.
