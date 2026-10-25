import pytest

from src.build import Tables
from src.catalog import Catalog, Scored
from src.constants import BASE_BY_STRENGTH, Status, Strength
from src.decide import Decider
from src.fuzzy import FuzzyAlias
from src.matchers import ExactAlias, FirstHit, JoinedWords, Query, WithoutNumbers
from src.models import Filters, Hints
from src.resolver import Resolver
from src.typos import TypoCorrector


def _query(text: str) -> Query:
    return Query(text, Hints(), Filters())


def _ids(scored: Scored) -> list[str]:
    return [entity_id for _, _, entity_id in scored]


class Exploding:
    def match(self, query: Query) -> Scored:
        raise AssertionError(f"called with {query.text}")


@pytest.fixture()
def exact(tables: Tables) -> ExactAlias:
    return ExactAlias(tables, Catalog(tables))


def test_exact_alias_hits_one_entity(exact: ExactAlias) -> None:
    assert _ids(exact.match(_query("aws eks"))) == ["aws/eks"]


def test_joined_words_finds_the_compound(exact: ExactAlias) -> None:
    assert _ids(JoinedWords(exact).match(_query("sentinel one"))) == ["sentinelone/sentinelone"]


def test_without_numbers_skips_vendor_entities(exact: ExactAlias, tables: Tables) -> None:
    assert WithoutNumbers(exact, Catalog(tables)).match(_query("microsoft 365")) == []


def test_without_numbers_caps_at_weak(exact: ExactAlias, tables: Tables) -> None:
    [(_, raw, entity_id)] = WithoutNumbers(exact, Catalog(tables)).match(_query("python 3"))
    assert (entity_id, raw) == ("python/python", BASE_BY_STRENGTH[Strength.WEAK])


def test_first_hit_stops_at_the_first_non_empty_matcher(exact: ExactAlias) -> None:
    assert _ids(FirstHit((exact, Exploding())).match(_query("aws eks"))) == ["aws/eks"]


def test_fuzzy_alias_fixes_a_typo(tables: Tables) -> None:
    fuzzy = FuzzyAlias(tables, Catalog(tables), TypoCorrector(tables.idf))
    assert _ids(fuzzy.match(_query("crowdstrik falcon")))[0] == "crowdstrike/falcon"


def test_decider_returns_no_match_for_no_candidates(tables: Tables) -> None:
    assert Decider(tables).decide([]).status is Status.NO_MATCH


def test_resolver_runs_the_injected_matcher(tables: Tables) -> None:
    assert Resolver(tables, matcher=FirstHit(())).resolve("AWS").status is Status.NO_MATCH
