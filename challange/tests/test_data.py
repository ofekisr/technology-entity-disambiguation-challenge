from src.constants import DATA_DIR
from src.models import load_sources

CATEGORY_LEAVES = 23
MIN_ENTITIES = 100
MAX_ENTITIES = 300


def test_categories_have_23_leaves() -> None:
    assert len(load_sources(DATA_DIR).categories) == CATEGORY_LEAVES


def test_entity_count_in_seed_range() -> None:
    assert MIN_ENTITIES <= len(load_sources(DATA_DIR).entities) <= MAX_ENTITIES


def test_every_entity_has_known_category() -> None:
    sources = load_sources(DATA_DIR)
    known = {leaf.id for leaf in sources.categories}
    assert all(entity.category in known for entity in sources.entities)


def test_concept_terms_map_to_one_concept_each() -> None:
    concepts = load_sources(DATA_DIR).concepts
    terms = [row.term for row in concepts]
    assert len(terms) == len(set(terms))
    assert {("kubernetes", "k8s"), ("kubernetes", "k8")} <= {(row.concept_id, row.term) for row in concepts}


def test_every_entity_has_a_concept_phrase() -> None:
    sources = load_sources(DATA_DIR)
    assert {row.entity_id for row in sources.entity_concepts} == {entity.id for entity in sources.entities}


def test_thresholds_match_d28() -> None:
    thresholds = load_sources(DATA_DIR).thresholds
    assert (thresholds.t_high, thresholds.t_low, thresholds.margin) == (0.75, 0.5, 0.15)
    assert (thresholds.top_k, thresholds.hint_bonus) == (20, 0.15)
