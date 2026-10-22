from collections.abc import Callable

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.build import Tables, build_tables
from src.constants import DATA_DIR, VENDOR_PRODUCT
from src.models import load_sources
from src.resolver import Resolver

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
