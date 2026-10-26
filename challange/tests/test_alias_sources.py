import pytest

from src.alias_sources import AliasSource, CanonicalNames, CategoryCombos, ConceptCombos, CuratedAliases, VendorNames, VendorProductCombos
from src.build import build_tables, entity_records
from src.constants import DATA_DIR, Strength
from src.models import EntityConceptRow, Sources, load_sources
from src.tables import EntityRecord


@pytest.fixture(scope="module")
def sources() -> Sources:
    return load_sources(DATA_DIR)


@pytest.fixture(scope="module")
def records(sources: Sources) -> dict[str, EntityRecord]:
    return entity_records(sources)


def _aliases_of(source: AliasSource, sources: Sources, records: dict[str, EntityRecord], entity_id: str) -> set[tuple[str, Strength]]:
    return {(alias, strength) for alias, target, strength in source.aliases(sources, records) if target == entity_id}


def test_canonical_names_give_canonical_and_weak_product(sources: Sources, records: dict[str, EntityRecord]) -> None:
    found = _aliases_of(CanonicalNames(), sources, records, "aws/eks")
    assert {("AWS EKS", Strength.CANONICAL), ("EKS", Strength.WEAK)} <= found


def test_vendor_product_combos_include_the_parent_vendor(sources: Sources, records: dict[str, EntityRecord]) -> None:
    assert ("Amazon EKS", Strength.GENERATED) in _aliases_of(VendorProductCombos(), sources, records, "aws/eks")


def test_category_combos_use_the_category_label(sources: Sources, records: dict[str, EntityRecord]) -> None:
    assert ("EKS Cloud Service", Strength.GENERATED) in _aliases_of(CategoryCombos(), sources, records, "aws/eks")


def test_vendor_names_point_to_the_flagship(sources: Sources, records: dict[str, EntityRecord]) -> None:
    assert ("Amazon Web Services", Strength.STRONG) in _aliases_of(VendorNames(), sources, records, "aws/aws")


def test_prefix_aliases_are_never_standalone(sources: Sources, records: dict[str, EntityRecord]) -> None:
    standalone = {alias for alias, _, _ in VendorNames().aliases(sources, records)}
    combos = _aliases_of(VendorProductCombos(), sources, records, "microsoft/teams")
    assert "MS" not in standalone and ("MS Teams", Strength.GENERATED) in combos


def test_curated_aliases_keep_their_strength(sources: Sources, records: dict[str, EntityRecord]) -> None:
    assert ("Elastic Kubernetes Service", Strength.STRONG) in _aliases_of(CuratedAliases(), sources, records, "aws/eks")


def test_concept_combos_pair_vendor_names_with_phrases(sources: Sources, records: dict[str, EntityRecord]) -> None:
    found = _aliases_of(ConceptCombos(), sources, records, "aws/eks")
    assert {("AWS managed kubernetes", Strength.GENERATED), ("Amazon managed kubernetes", Strength.GENERATED)} <= found


def test_concept_combos_never_emit_the_bare_phrase(sources: Sources, records: dict[str, EntityRecord]) -> None:
    assert "managed kubernetes" not in {alias for alias, _ in _aliases_of(ConceptCombos(), sources, records, "aws/eks")}


def test_concept_combos_skip_low_weight_edges(sources: Sources, records: dict[str, EntityRecord]) -> None:
    faint = EntityConceptRow(entity_id="aws/eks", phrase="kubernetes", weight=sources.thresholds.concept_min_weight / 2)
    assert list(ConceptCombos().aliases(sources.model_copy(update={"entity_concepts": (faint,)}), records)) == []


def test_build_runs_only_the_given_sources(sources: Sources) -> None:
    aliases = build_tables(sources, alias_sources=(CuratedAliases(),)).aliases
    assert "elastic kubernetes service" in aliases and "aws eks" not in aliases


def _concept_strengths(edge: EntityConceptRow, sources: Sources, records: dict[str, EntityRecord]) -> set[Strength]:
    only_edge = sources.model_copy(update={"entity_concepts": (edge,)})
    return {strength for _, _, strength in ConceptCombos().aliases(only_edge, records)}


def test_concept_combos_take_their_tier_from_the_edge_weight(sources: Sources, records: dict[str, EntityRecord]) -> None:
    full = EntityConceptRow(entity_id="aws/eks", phrase="managed kubernetes", weight=sources.thresholds.concept_generated_weight)
    partial = full.model_copy(update={"weight": sources.thresholds.concept_min_weight})
    assert _concept_strengths(full, sources, records) == {Strength.GENERATED}
    assert _concept_strengths(partial, sources, records) == {Strength.WEAK}
