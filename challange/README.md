# Technology Entity Resolver

Deterministic, dictionary-first resolver that maps technology names from threat reports to stable canonical ids.
Design: [DESIGN.md](DESIGN.md) · diagrams: [architecture](docs/architecture.md), [resolve flow](docs/resolve-flow.md).

## Run (Python 3.12)

```bash
make setup
make test
make resolve NAME="Amazon Web Services"
```

`make eval` prints precision, coverage, F1, latency, a threshold sweep and the reliability table.

## Run (Docker)

```bash
docker build -t tech-resolver .
docker run --rm tech-resolver idx resolve "AWS EKS"
```

## Interface

```python
from src.resolver import resolve
from src.models import Hints, Filters

resolve("Sentinel")                                   # ambiguous + alternatives
resolve("Sentinel", hints=Hints(vendor="Microsoft"))  # resolved: microsoft/sentinel
resolve("AWS EKS", filters=Filters(vendors=("aws",)))
```

CLI: `idx build | validate | resolve NAME | eval | add-alias ENTITY_ID ALIAS`.
Source of truth: `src/data/` (`categories.yaml`, `vendors.csv`, `entities.jsonl`, `aliases.csv`, `thresholds.yaml`).
