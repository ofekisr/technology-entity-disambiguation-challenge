from collections.abc import Iterator
from typing import Protocol

from src.constants import UNCATEGORIZED, VENDOR_CATEGORY, Strength
from src.models import Sources, VendorRow
from src.tables import AliasTriple, EntityRecord, vendor_entity_id

GENERATED_SKIP_CATEGORIES = frozenset({VENDOR_CATEGORY, UNCATEGORIZED})

Records = dict[str, EntityRecord]


class AliasSource(Protocol):
    def aliases(self, sources: Sources, records: Records) -> Iterator[AliasTriple]: ...


class CanonicalNames:
    def aliases(self, sources: Sources, records: Records) -> Iterator[AliasTriple]:
        for entity in sources.entities:
            yield records[entity.id].canonical_name, entity.id, Strength.CANONICAL
            yield entity.product, entity.id, Strength.WEAK


class VendorProductCombos:
    def aliases(self, sources: Sources, records: Records) -> Iterator[AliasTriple]:
        vendors = {vendor.vendor_id: vendor for vendor in sources.vendors}
        for entity in sources.entities:
            for name in _names_with_parent(vendors, entity.vendor_id):
                yield f"{name} {entity.product}", entity.id, Strength.GENERATED


class CategoryCombos:
    def aliases(self, sources: Sources, records: Records) -> Iterator[AliasTriple]:
        labels = {leaf.id: leaf.label for leaf in sources.categories}
        for entity in sources.entities:
            if entity.category not in GENERATED_SKIP_CATEGORIES:
                yield f"{entity.product} {labels[entity.category]}", entity.id, Strength.GENERATED


class VendorNames:
    def aliases(self, sources: Sources, records: Records) -> Iterator[AliasTriple]:
        for vendor in sources.vendors:
            target = vendor.flagship_entity_id or vendor_entity_id(vendor.vendor_id)
            yield vendor.name, target, Strength.CANONICAL
            for alias in vendor.aliases:
                yield alias, target, Strength.STRONG


class ConceptCombos:
    def aliases(self, sources: Sources, records: Records) -> Iterator[AliasTriple]:
        vendors = {vendor.vendor_id: vendor for vendor in sources.vendors}
        floor = sources.thresholds.concept_min_weight
        for row in sources.entity_concepts:
            if row.weight >= floor and row.entity_id in records:
                for name in _names_with_parent(vendors, records[row.entity_id].vendor_id):
                    yield f"{name} {row.phrase}", row.entity_id, Strength.WEAK


class CuratedAliases:
    def aliases(self, sources: Sources, records: Records) -> Iterator[AliasTriple]:
        for row in sources.aliases:
            yield row.alias, row.entity_id, row.strength


DEFAULT_ALIAS_SOURCES: tuple[AliasSource, ...] = (
    CanonicalNames(),
    VendorProductCombos(),
    CategoryCombos(),
    VendorNames(),
    CuratedAliases(),
    ConceptCombos(),
)


def vendor_names(vendor: VendorRow) -> tuple[str, ...]:
    return (vendor.name, *vendor.aliases)


def prefix_names(vendor: VendorRow) -> tuple[str, ...]:
    return (*vendor_names(vendor), *vendor.prefix_aliases)


def _names_with_parent(vendors: dict[str, VendorRow], vendor_id: str) -> tuple[str, ...]:
    vendor = vendors[vendor_id]
    parent = vendors.get(vendor.parent_vendor_id or "")
    return (*prefix_names(vendor), *(prefix_names(parent) if parent else ()))
