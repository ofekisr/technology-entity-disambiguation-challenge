from dataclasses import dataclass
from typing import Protocol

from src.models import Filters, Hints, Resolution


@dataclass(frozen=True)
class LedgerKey:
    input_norm: str
    hints: Hints
    filters: Filters
    index_version: str


class ResponseLedger(Protocol):
    def get(self, key: LedgerKey) -> Resolution | None: ...

    def record(self, key: LedgerKey, resolution: Resolution) -> None: ...


class InMemoryLedger:
    # Production stub (D-17, D-30, D-31): a durable append-only store (Postgres / DynamoDB) keyed by
    # LedgerKey, seeding the LRU with the top-1,000 keys by 30-day traffic. A new index_version never
    # overwrites old rows; the replay diff between versions is the publish gate in Flow A.
    def __init__(self) -> None:
        self._rows: dict[LedgerKey, Resolution] = {}

    def get(self, key: LedgerKey) -> Resolution | None:
        return self._rows.get(key)

    def record(self, key: LedgerKey, resolution: Resolution) -> None:
        self._rows.setdefault(key, resolution)


class ReviewQueue(Protocol):
    def enqueue(self, input_norm: str, index_version: str) -> None: ...

    def pending(self) -> tuple[tuple[str, str], ...]: ...


class InMemoryReviewQueue:
    # Human review workflow stub (D-13, D-47): unknown inputs land in a queue ranked by
    # traffic_7d x severity (D-25); a curator answers with `idx add-alias` or a new entity in a PR,
    # CODEOWNERS approve, and Flow A publishes the next snapshot. The runtime never mints ids.
    def __init__(self) -> None:
        self._items: dict[tuple[str, str], None] = {}

    def enqueue(self, input_norm: str, index_version: str) -> None:
        self._items.setdefault((input_norm, index_version), None)

    def pending(self) -> tuple[tuple[str, str], ...]:
        return tuple(self._items)


@dataclass(frozen=True)
class Proposal:
    plugin_id: str
    alias: str
    entity_id: str
    evidence_url: str


class EnrichmentPlugin(Protocol):
    # Enrichment port, doc only (D-24, D-37): plugins propose changesets and never write the index.
    # Deterministic plugins may run inside `idx build`; external / LLM plugins run in `idx propose`,
    # pin model + prompt hash, write proposals/<plugin_id>/<YYYY-MM-DD>.jsonl, and go to review.
    def propose(self, scope: str) -> list[Proposal]: ...


# Monitoring stub (D-25, D-39): emit per-request status, latency and index_version; alert on
# unresolved > 5 %, ambiguous > 3 %, p99 > 5 ms, source age > 30 days; rank index-health work
# by traffic x severity.
# Real-time overlay stub (Flow D, D-43): append-only exact aliases admitted only when the ledger
# replay shows no changed answer; index_version would become snapshot_hash + overlay_seq.
