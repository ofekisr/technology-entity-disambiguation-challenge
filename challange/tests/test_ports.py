from src.models import Filters, Hints, Resolution
from src.ports import InMemoryLedger, InMemoryReviewQueue, LedgerKey


def test_ledger_round_trips_by_key() -> None:
    ledger = InMemoryLedger()
    key = LedgerKey("aws foo", Hints(), Filters(), "v1")
    answer = Resolution.no_match("v1")
    ledger.record(key, answer)
    assert ledger.get(key) == answer
    assert ledger.get(LedgerKey("aws foo", Hints(), Filters(), "v2")) is None


def test_review_queue_keeps_order_and_dedupes() -> None:
    queue = InMemoryReviewQueue()
    for name in ("b", "a", "b"):
        queue.enqueue(name, "v1")
    assert queue.pending() == (("b", "v1"), ("a", "v1"))
