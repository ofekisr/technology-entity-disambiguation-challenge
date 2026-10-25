import hashlib
import json
import math
from collections import defaultdict
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import asdict

from src.alias_sources import DEFAULT_ALIAS_SOURCES, AliasSource, vendor_names
from src.constants import (
    BIN_EDGE_DECIMALS,
    FULL_CONFIDENCE,
    CALIBRATION_BINS,
    EXACT_ONLY_MAX_LEN,
    STRENGTH_RANK,
    VENDOR_CATEGORY,
    Strength,
)
from src.models import EntityRow, Sources, VendorRow
from src.normalize import normalize
from src.tables import AliasHit, AliasTriple, EntityRecord, Tables, canonical_name, vendor_entity_id

STRONG_RANK = STRENGTH_RANK[Strength.STRONG]
VENDOR_TIER = 1


def entity_records(sources: Sources) -> dict[str, EntityRecord]:
    vendors = {vendor.vendor_id: vendor for vendor in sources.vendors}
    records = [_product_record(entity, vendors[entity.vendor_id]) for entity in sources.entities]
    records += [_vendor_record(vendor) for vendor in sources.vendors]
    return {record.id: record for record in sorted(records, key=lambda record: record.id)}


def _product_record(entity: EntityRow, vendor: VendorRow) -> EntityRecord:
    name = canonical_name(vendor.name, entity.product)
    return EntityRecord(entity.id, vendor.vendor_id, vendor.name, name, entity.category, entity.tier)


def _vendor_record(vendor: VendorRow) -> EntityRecord:
    entity_id = vendor_entity_id(vendor.vendor_id)
    return EntityRecord(entity_id, vendor.vendor_id, vendor.name, vendor.name, VENDOR_CATEGORY, VENDOR_TIER)


def _all_aliases(sources: Sources, records: dict[str, EntityRecord], alias_sources: Sequence[AliasSource]) -> Iterator[AliasTriple]:
    for source in alias_sources:
        yield from source.aliases(sources, records)


def _demote_short(alias_norm: str, strength: Strength) -> Strength:
    return Strength.WEAK if len(alias_norm) <= EXACT_ONLY_MAX_LEN else strength


def _strongest_per_entity(triples: Iterable[AliasTriple]) -> dict[str, dict[str, Strength]]:
    merged: dict[str, dict[str, Strength]] = defaultdict(dict)
    for alias, entity_id, strength in triples:
        alias_norm = normalize(alias)
        strength = _demote_short(alias_norm, strength)
        current = merged[alias_norm].get(entity_id, Strength.WEAK)
        if alias_norm and STRENGTH_RANK[strength] >= STRENGTH_RANK[current]:
            merged[alias_norm][entity_id] = strength
    return merged


def _shadow(hits: dict[str, Strength]) -> tuple[AliasHit, ...]:
    has_manual = any(STRENGTH_RANK[strength] >= STRONG_RANK for strength in hits.values())
    kept = {
        entity_id: strength
        for entity_id, strength in hits.items()
        if not has_manual or STRENGTH_RANK[strength] >= STRONG_RANK
    }
    return tuple(AliasHit(entity_id, kept[entity_id]) for entity_id in sorted(kept))


def build_alias_index(
    sources: Sources, records: dict[str, EntityRecord], alias_sources: Sequence[AliasSource] = DEFAULT_ALIAS_SOURCES
) -> dict[str, tuple[AliasHit, ...]]:
    merged = _strongest_per_entity(_all_aliases(sources, records, alias_sources))
    return {alias_norm: _shadow(merged[alias_norm]) for alias_norm in sorted(merged)}


def build_vendor_aliases(sources: Sources) -> dict[str, str]:
    pairs = sorted(
        (normalize(name), vendor.vendor_id) for vendor in sources.vendors for name in vendor_names(vendor)
    )
    index: dict[str, str] = {}
    for alias_norm, vendor_id in pairs:
        index.setdefault(alias_norm, vendor_id)
    return index


def build_postings(aliases: dict[str, tuple[AliasHit, ...]]) -> dict[str, tuple[str, ...]]:
    postings: dict[str, set[str]] = defaultdict(set)
    for alias_norm in aliases:
        if len(alias_norm) > EXACT_ONLY_MAX_LEN:
            for token in alias_norm.split():
                postings[token].add(alias_norm)
    return {token: tuple(sorted(postings[token])) for token in sorted(postings)}


def build_idf(postings: dict[str, tuple[str, ...]]) -> dict[str, float]:
    total = len({alias for aliases in postings.values() for alias in aliases})
    return {token: math.log1p(total / len(aliases)) for token, aliases in postings.items()}


def build_synonyms(sources: Sources) -> dict[str, str]:
    pairs = sorted((row.term, row.concept_id) for row in sources.concepts if row.term != row.concept_id)
    return dict(pairs)


def identity_calibration() -> tuple[tuple[float, float, float], ...]:
    width = 1.0 / CALIBRATION_BINS
    return tuple(
        (round(i * width, BIN_EDGE_DECIMALS), round((i + 1) * width, BIN_EDGE_DECIMALS), FULL_CONFIDENCE)
        for i in range(CALIBRATION_BINS)
    )


def content_hash(tables: Tables) -> str:
    payload = asdict(tables) | {"index_version": ""}
    encoded = json.dumps(payload, sort_keys=True, default=str).encode()
    return hashlib.sha256(encoded).hexdigest()[:16]


def build_tables(sources: Sources, alias_sources: Sequence[AliasSource] = DEFAULT_ALIAS_SOURCES) -> Tables:
    records = entity_records(sources)
    aliases = build_alias_index(sources, records, alias_sources)
    postings = build_postings(aliases)
    draft = Tables(
        entities=records,
        aliases=aliases,
        vendor_aliases=build_vendor_aliases(sources),
        postings=postings,
        idf=build_idf(postings),
        synonyms=build_synonyms(sources),
        thresholds=sources.thresholds,
        calibration=identity_calibration(),
    )
    return Tables(**{**draft.__dict__, "index_version": content_hash(draft)})


def _alias_errors(tables: Tables) -> Iterator[str]:
    for alias_norm, hits in tables.aliases.items():
        strong = [hit for hit in hits if STRENGTH_RANK[hit.strength] >= STRONG_RANK]
        if len(strong) > 1:
            yield f"strong alias '{alias_norm}' maps to {[hit.entity_id for hit in strong]}"
        for hit in hits:
            if hit.entity_id not in tables.entities:
                yield f"alias '{alias_norm}' points to unknown entity {hit.entity_id}"


def _vendor_errors(sources: Sources) -> Iterator[str]:
    parents = {vendor.vendor_id: vendor.parent_vendor_id for vendor in sources.vendors}
    for vendor_id in parents:
        seen, current = {vendor_id}, parents[vendor_id]
        while current:
            if current in seen or current not in parents:
                yield f"vendor {vendor_id}: parent cycle or unknown parent at {current}"
                break
            seen.add(current)
            current = parents[current]


def _entity_errors(sources: Sources) -> Iterator[str]:
    vendors = {vendor.vendor_id for vendor in sources.vendors}
    categories = {leaf.id for leaf in sources.categories}
    for entity in sources.entities:
        if entity.vendor_id not in vendors or entity.category not in categories:
            yield f"entity {entity.id}: unknown vendor or category"
        if not entity.id.startswith(f"{entity.vendor_id}/"):
            yield f"entity {entity.id}: id does not start with its vendor"


def _concept_errors(sources: Sources) -> Iterator[str]:
    concepts = {row.concept_id for row in sources.concepts}
    entities = {entity.id for entity in sources.entities}
    for row in sources.entity_concepts:
        if row.entity_id not in entities:
            yield f"concept phrase '{row.phrase}' points to unknown entity {row.entity_id}"
        unknown = sorted(set(normalize(row.phrase).split()) - concepts)
        if unknown:
            yield f"entity {row.entity_id}: unknown concept {unknown} in '{row.phrase}'"


def validate(sources: Sources, tables: Tables) -> list[str]:
    return [*_alias_errors(tables), *_vendor_errors(sources), *_entity_errors(sources), *_concept_errors(sources)]
