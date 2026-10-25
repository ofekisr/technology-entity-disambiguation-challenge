from src.build import Tables
from src.constants import UNCATEGORIZED, VENDOR_CATEGORY
from src.models import Filters, Hints

Candidate = tuple[float, float, str]
Scored = list[Candidate]


class Catalog:
    def __init__(self, tables: Tables) -> None:
        self.tables = tables

    def passes(self, entity_id: str, filters: Filters) -> bool:
        record = self.tables.entities[entity_id]
        vendor_ok = not filters.vendors or record.vendor_id in filters.vendors
        uncategorized_ok = filters.include_uncategorized and record.category == UNCATEGORIZED
        category_ok = not filters.categories or record.category in filters.categories or uncategorized_ok
        return vendor_ok and category_ok

    def boosted(self, score: float, entity_id: str, hints: Hints) -> Candidate:
        return score + self._bonus(entity_id, hints), score, entity_id

    def is_vendor(self, entity_id: str) -> bool:
        return self.tables.entities[entity_id].category == VENDOR_CATEGORY

    def _bonus(self, entity_id: str, hints: Hints) -> float:
        record = self.tables.entities[entity_id]
        matches = hints.vendor == record.vendor_id or hints.category == record.category
        return self.tables.thresholds.hint_bonus if matches else 0.0
