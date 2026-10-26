from collections.abc import Callable

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.build import build_tables
from src.constants import DATA_DIR, FULL_CONFIDENCE, VENDOR_PRODUCT
from src.decide import Decider
from src.models import load_sources
from src.resolver import Resolver
from src.tables import Tables

TABLES: Tables = build_tables(load_sources(DATA_DIR))
RESOLVER = Resolver(TABLES)
FLAGSHIP_SHADOWED = {f"{v.vendor_id}/{VENDOR_PRODUCT}" for v in load_sources(DATA_DIR).vendors if v.flagship_entity_id}
ENTITIES = [record for record in TABLES.entities.values() if record.id not in FLAGSHIP_SHADOWED]
NAMES = st.sampled_from([record.canonical_name for record in ENTITIES])
EXAMPLES = 60


@pytest.mark.parametrize("entity_id", [record.id for record in ENTITIES])
def test_resolve_canonical_is_canonical(entity_id: str) -> None:
    record = TABLES.entities[entity_id]
    assert RESOLVER.resolve(record.canonical_name).id == entity_id


@settings(max_examples=EXAMPLES)
@given(NAMES)
def test_idempotent(name: str) -> None:
    assert RESOLVER.resolve(name) == Resolver(TABLES).resolve(name)


@settings(max_examples=EXAMPLES)
@given(NAMES, st.sampled_from([str.upper, str.lower, str.title]))
def test_casing_invariant(name: str, case: Callable[[str], str]) -> None:
    assert RESOLVER.resolve(case(name)).id == RESOLVER.resolve(name).id


@settings(max_examples=EXAMPLES)
@given(NAMES, st.sampled_from([".", ",", "!", " -", " ()"]))
def test_punctuation_invariant(name: str, mark: str) -> None:
    assert RESOLVER.resolve(name + mark).id == RESOLVER.resolve(name).id


@settings(max_examples=EXAMPLES)
@given(NAMES, st.sampled_from([" 2.14", " v7", " 10.0.1"]))
def test_version_invariant(name: str, version: str) -> None:
    assert RESOLVER.resolve(name + version).id == RESOLVER.resolve(name).id


RAW_SCORES = st.floats(min_value=0.0, max_value=FULL_CONFIDENCE)
BONUSES = st.sampled_from((0.0, TABLES.thresholds.hint_bonus))
CANDIDATES = st.lists(st.tuples(RAW_SCORES, BONUSES, st.sampled_from(sorted(TABLES.entities))), min_size=1, max_size=5, unique_by=lambda c: c[2])


@settings(max_examples=EXAMPLES)
@given(CANDIDATES)
def test_confidence_stays_within_zero_and_one_when_rank_exceeds_one(candidates: list[tuple[float, float, str]]) -> None:
    result = Decider(TABLES).decide([(raw + bonus, raw, entity_id) for raw, bonus, entity_id in candidates])
    assert 0.0 <= result.confidence <= FULL_CONFIDENCE
    assert all(0.0 <= alternative.confidence <= FULL_CONFIDENCE for alternative in result.alternatives)
