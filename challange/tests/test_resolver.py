from src.build import Tables
from src.constants import Status
from src.models import Filters, Hints
from src.ports import InMemoryLedger, InMemoryReviewQueue, LedgerKey
from src.resolver import Resolver, resolve


def test_vendor_hint_breaks_the_sentinel_tie(resolver: Resolver) -> None:
    result = resolver.resolve("Sentinel", hints=Hints(vendor="Microsoft"))
    assert (result.id, result.status) == ("microsoft/sentinel", Status.RESOLVED)


def test_category_hint_breaks_the_falcon_tie(resolver: Resolver) -> None:
    assert resolver.resolve("Falcon", hints=Hints(category="edr")).id == "crowdstrike/falcon"


def test_exact_strong_hit_ignores_contradicting_hint(resolver: Resolver) -> None:
    result = resolver.resolve("Microsoft Sentinel", hints=Hints(vendor="HashiCorp"))
    assert (result.id, result.confidence) == ("microsoft/sentinel", 1.0)


def test_filters_drop_other_vendors(resolver: Resolver) -> None:
    result = resolver.resolve("Sentinel", filters=Filters(vendors=("hashicorp",)))
    assert result.id == "hashicorp/sentinel"


def test_filter_that_removes_everything_is_no_match(resolver: Resolver) -> None:
    assert resolver.resolve("AWS EKS", filters=Filters(vendors=("microsoft",))).status is Status.NO_MATCH


def test_no_match_lands_in_review_queue(tables: Tables) -> None:
    queue = InMemoryReviewQueue()
    Resolver(tables, review_queue=queue).resolve("Totally Unknown Thing")
    assert queue.pending() == (("totally unknown thing", tables.index_version),)


def test_ledger_answer_wins(tables: Tables) -> None:
    ledger = InMemoryLedger()
    recorded = Resolver(tables).resolve("AWS")
    ledger.record(LedgerKey("eks", Hints(), Filters(), tables.index_version), recorded)
    assert Resolver(tables, ledger=ledger).resolve("EKS") == recorded


def test_typo_beyond_two_edits_is_not_corrected(resolver: Resolver) -> None:
    assert resolver.resolve("Crwdstrk Falcon").id != "crowdstrike/falcon"


def test_short_tokens_are_never_typo_corrected(resolver: Resolver) -> None:
    assert resolver.resolve("EKX").status is Status.NO_MATCH


def test_vendor_prefix_with_extra_token_still_resolves(resolver: Resolver) -> None:
    assert resolver.resolve("CrowdStrike Falcon Sensor").id == "crowdstrike/falcon"


def test_module_level_resolve_carries_index_version() -> None:
    result = resolve("AWS")
    assert result.id == "aws/aws"
    assert len(result.index_version) > 0
