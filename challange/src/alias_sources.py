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
            vendor = vendors[entity.vendor_id]
            parent = vendors.get(vendor.parent_vendor_id or "")
            for name in (*vendor_names(vendor), *(vendor_names(parent) if parent else ())):
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
)


def vendor_names(vendor: VendorRow) -> tuple[str, ...]:
    return (vendor.name, *vendor.aliases)
