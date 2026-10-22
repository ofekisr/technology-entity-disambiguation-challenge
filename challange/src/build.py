import hashlib
import json
import math
import sqlite3
from collections import defaultdict
from collections.abc import Iterable, Iterator
from dataclasses import asdict, dataclass, field
from pathlib import Path

from src.constants import (
    BIN_EDGE_DECIMALS,
    FULL_CONFIDENCE,
    CALIBRATION_BINS,
    EXACT_ONLY_MAX_LEN,
    STRENGTH_RANK,
    UNCATEGORIZED,
    VENDOR_CATEGORY,
    VENDOR_PRODUCT,
    Strength,
)
from src.models import EntityRow, Sources, Thresholds, VendorRow
from src.normalize import normalize, tokens

GENERATED_SKIP_CATEGORIES = frozenset({VENDOR_CATEGORY, UNCATEGORIZED})
STRONG_RANK = STRENGTH_RANK[Strength.STRONG]
VENDOR_TIER = 1


@dataclass(frozen=True)
class EntityRecord:
    id: str
    vendor_id: str
    vendor_name: str
    canonical_name: str
    category: str
    tier: int


@dataclass(frozen=True)
class AliasHit:
    entity_id: str
    strength: Strength


@dataclass(frozen=True)
class Tables:
    entities: dict[str, EntityRecord]
    aliases: dict[str, tuple[AliasHit, ...]]
    vendor_aliases: dict[str, str]
    postings: dict[str, tuple[str, ...]]
    idf: dict[str, float]
    thresholds: Thresholds
    calibration: tuple[tuple[float, float, float], ...]
    index_version: str = field(default="")


AliasTriple = tuple[str, str, Strength]


def canonical_name(vendor_name: str, product: str) -> str:
    if tokens(product)[: len(tokens(vendor_name))] == tokens(vendor_name):
        return product
    return f"{vendor_name} {product}"


def vendor_entity_id(vendor_id: str) -> str:
    return f"{vendor_id}/{VENDOR_PRODUCT}"


def _entity_records(sources: Sources) -> dict[str, EntityRecord]:
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


def _vendor_names(vendor: VendorRow) -> tuple[str, ...]:
    return (vendor.name, *vendor.aliases)


def _product_aliases(entity: EntityRow, sources: Sources, records: dict[str, EntityRecord]) -> Iterator[AliasTriple]:
    vendors = {vendor.vendor_id: vendor for vendor in sources.vendors}
    vendor = vendors[entity.vendor_id]
    yield records[entity.id].canonical_name, entity.id, Strength.CANONICAL
    yield entity.product, entity.id, Strength.WEAK
    for name in _vendor_names(vendor):
        yield f"{name} {entity.product}", entity.id, Strength.GENERATED
    parent = vendors.get(vendor.parent_vendor_id or "")
    for name in _vendor_names(parent) if parent else ():
        yield f"{name} {entity.product}", entity.id, Strength.GENERATED
    yield from _category_aliases(entity, sources)


def _category_aliases(entity: EntityRow, sources: Sources) -> Iterator[AliasTriple]:
    if entity.category in GENERATED_SKIP_CATEGORIES:
        return
    label = next(leaf.label for leaf in sources.categories if leaf.id == entity.category)
    yield f"{entity.product} {label}", entity.id, Strength.GENERATED


def _vendor_entity_aliases(vendor: VendorRow) -> Iterator[AliasTriple]:
    target = vendor.flagship_entity_id or vendor_entity_id(vendor.vendor_id)
    yield vendor.name, target, Strength.CANONICAL
    for alias in vendor.aliases:
        yield alias, target, Strength.STRONG


def _all_aliases(sources: Sources, records: dict[str, EntityRecord]) -> Iterator[AliasTriple]:
    for entity in sources.entities:
        yield from _product_aliases(entity, sources, records)
    for vendor in sources.vendors:
        yield from _vendor_entity_aliases(vendor)
    for row in sources.aliases:
        yield row.alias, row.entity_id, row.strength


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


def build_alias_index(sources: Sources, records: dict[str, EntityRecord]) -> dict[str, tuple[AliasHit, ...]]:
    merged = _strongest_per_entity(_all_aliases(sources, records))
    return {alias_norm: _shadow(merged[alias_norm]) for alias_norm in sorted(merged)}


def build_vendor_aliases(sources: Sources) -> dict[str, str]:
    pairs = sorted(
        (normalize(name), vendor.vendor_id) for vendor in sources.vendors for name in _vendor_names(vendor)
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


def build_tables(sources: Sources) -> Tables:
    records = _entity_records(sources)
    aliases = build_alias_index(sources, records)
    postings = build_postings(aliases)
    draft = Tables(
        entities=records,
        aliases=aliases,
        vendor_aliases=build_vendor_aliases(sources),
        postings=postings,
        idf=build_idf(postings),
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


def validate(sources: Sources, tables: Tables) -> list[str]:
    return [*_alias_errors(tables), *_vendor_errors(sources), *_entity_errors(sources)]


SCHEMA = (
    "CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)",
    "CREATE TABLE entities (id TEXT PRIMARY KEY, vendor_id TEXT, vendor_name TEXT,"
    " canonical_name TEXT, category TEXT, tier INTEGER)",
    "CREATE TABLE aliases (alias_norm TEXT, entity_id TEXT, strength TEXT, PRIMARY KEY (alias_norm, entity_id))",
    "CREATE TABLE vendor_aliases (alias_norm TEXT PRIMARY KEY, vendor_id TEXT)",
    "CREATE TABLE postings (token TEXT, alias_norm TEXT, PRIMARY KEY (token, alias_norm))",
    "CREATE TABLE idf (token TEXT PRIMARY KEY, idf REAL)",
)


def write_snapshot(tables: Tables, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.unlink(missing_ok=True)
    with sqlite3.connect(path) as db:
        for statement in SCHEMA:
            db.execute(statement)
        _write_rows(db, tables)


def _write_rows(db: sqlite3.Connection, tables: Tables) -> None:
    meta = {
        "index_version": tables.index_version,
        "thresholds": tables.thresholds.model_dump_json(),
        "calibration": json.dumps(tables.calibration),
    }
    db.executemany("INSERT INTO meta VALUES (?, ?)", meta.items())
    db.executemany("INSERT INTO entities VALUES (?, ?, ?, ?, ?, ?)", [tuple(asdict(e).values()) for e in tables.entities.values()])
    db.executemany("INSERT INTO aliases VALUES (?, ?, ?)", _alias_rows(tables))
    db.executemany("INSERT INTO vendor_aliases VALUES (?, ?)", tables.vendor_aliases.items())
    db.executemany("INSERT INTO postings VALUES (?, ?)", _posting_rows(tables))
    db.executemany("INSERT INTO idf VALUES (?, ?)", tables.idf.items())


def _alias_rows(tables: Tables) -> Iterator[tuple[str, str, str]]:
    for alias_norm, hits in tables.aliases.items():
        for hit in hits:
            yield alias_norm, hit.entity_id, hit.strength.value


def _posting_rows(tables: Tables) -> Iterator[tuple[str, str]]:
    for token, aliases in tables.postings.items():
        for alias_norm in aliases:
            yield token, alias_norm


def load_snapshot(path: Path) -> Tables:
    with sqlite3.connect(path) as db:
        meta = dict(db.execute("SELECT key, value FROM meta"))
        tables = Tables(
            entities=_load_entities(db),
            aliases=_load_grouped(db, "SELECT alias_norm, entity_id, strength FROM aliases ORDER BY 1, 2"),
            vendor_aliases=dict(db.execute("SELECT alias_norm, vendor_id FROM vendor_aliases ORDER BY 1")),
            postings=_load_postings(db),
            idf=dict(db.execute("SELECT token, idf FROM idf ORDER BY 1")),
            thresholds=Thresholds.model_validate_json(meta["thresholds"]),
            calibration=tuple(tuple(row) for row in json.loads(meta["calibration"])),
            index_version=meta["index_version"],
        )
    if content_hash(tables) != tables.index_version:
        raise ValueError(f"snapshot {path} does not match its index_version")
    return tables


def _load_entities(db: sqlite3.Connection) -> dict[str, EntityRecord]:
    rows = db.execute("SELECT * FROM entities ORDER BY id")
    return {row[0]: EntityRecord(*row) for row in rows}


def _load_grouped(db: sqlite3.Connection, query: str) -> dict[str, tuple[AliasHit, ...]]:
    grouped: dict[str, list[AliasHit]] = defaultdict(list)
    for alias_norm, entity_id, strength in db.execute(query):
        grouped[alias_norm].append(AliasHit(entity_id, Strength(strength)))
    return {alias_norm: tuple(hits) for alias_norm, hits in grouped.items()}


def _load_postings(db: sqlite3.Connection) -> dict[str, tuple[str, ...]]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for token, alias_norm in db.execute("SELECT token, alias_norm FROM postings ORDER BY 1, 2"):
        grouped[token].append(alias_norm)
    return {token: tuple(aliases) for token, aliases in grouped.items()}
