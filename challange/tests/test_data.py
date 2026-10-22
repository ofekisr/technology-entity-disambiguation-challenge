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


def test_thresholds_match_d28() -> None:
    thresholds = load_sources(DATA_DIR).thresholds
    assert (thresholds.t_high, thresholds.t_low, thresholds.margin) == (0.75, 0.5, 0.15)
    assert (thresholds.top_k, thresholds.hint_bonus) == (20, 0.15)
