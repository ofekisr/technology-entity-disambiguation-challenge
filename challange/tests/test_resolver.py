from src.constants import Status
from src.models import Filters, Hints, Resolution
from src.ports import InMemoryLedger, InMemoryReviewQueue, LedgerKey
from src.resolver import Resolver, resolve
from src.tables import Tables


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


def test_vendor_prefix_with_extra_token_is_ambiguous(resolver: Resolver) -> None:
    result = resolver.resolve("CrowdStrike Falcon Sensor")
    assert (result.status, result.alternatives[0].id) == (Status.AMBIGUOUS, "crowdstrike/falcon")


def test_inferred_vendor_bonus_cannot_resolve_a_sibling(resolver: Resolver) -> None:
    for name in ("Splunk Enterprise Security", "Microsoft Defender for Cloud"):
        assert resolver.resolve(name).status is not Status.RESOLVED


def test_vendor_plus_number_is_not_the_vendor(resolver: Resolver) -> None:
    assert resolver.resolve("Microsoft 365").id is None


def test_product_plus_release_number_keeps_the_product(resolver: Resolver) -> None:
    assert resolver.resolve("Windows 10").id == "microsoft/windows"
    assert resolver.resolve("Python 3").id == "python/python"


def test_split_compound_matches_the_joined_alias(resolver: Resolver) -> None:
    assert resolver.resolve("Sentinel One").id == "sentinelone/sentinelone"
    assert resolver.resolve("sentinel-one").id == "sentinelone/sentinelone"
    assert resolver.resolve("Crowd Strike Falcon").id == "crowdstrike/falcon"


def test_vendor_plus_concept_phrase_resolves(resolver: Resolver) -> None:
    assert resolver.resolve("AWS managed Kubernetes").id == "aws/eks"
    assert resolver.resolve("Fortinet firewall").id == "fortinet/fortigate"


def test_hint_bonus_does_not_lift_a_weak_fuzzy_score_to_resolved(resolver: Resolver) -> None:
    result = resolver.resolve("Splunk Enterprise Security", hints=Hints(vendor="Splunk"))
    assert result.status is not Status.RESOLVED


def test_module_level_resolve_carries_index_version() -> None:
    result = resolve("AWS")
    assert result.id == "aws/aws"
    assert len(result.index_version) > 0


def test_four_char_token_accepts_one_edit_only(resolver: Resolver) -> None:
    assert resolver.resolve("Jirq").id == "atlassian/jira"
    assert resolver.resolve("Jiqq").status is Status.NO_MATCH


class CountingLedger(InMemoryLedger):
    def __init__(self) -> None:
        super().__init__()
        self.keys: list[LedgerKey] = []

    def record(self, key: LedgerKey, resolution: Resolution) -> None:
        self.keys.append(key)
        super().record(key, resolution)


def test_filters_order_does_not_change_the_key(tables: Tables) -> None:
    ledger = CountingLedger()
    resolver = Resolver(tables, ledger=ledger)
    resolver.resolve("Sentinel", filters=Filters(vendors=("thales", "hashicorp")))
    resolver.resolve("Sentinel", filters=Filters(vendors=("hashicorp", "thales")))
    assert len(ledger.keys) == 1


def test_empty_input_is_not_queued(tables: Tables) -> None:
    queue = InMemoryReviewQueue()
    Resolver(tables, review_queue=queue).resolve("!!!")
    assert queue.pending() == ()
