import json
import sqlite3
from collections import defaultdict
from collections.abc import Iterator
from dataclasses import asdict
from pathlib import Path

from src.build import content_hash
from src.constants import Strength
from src.models import Thresholds
from src.tables import AliasHit, EntityRecord, Tables

SCHEMA = (
    "CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)",
    "CREATE TABLE entities (id TEXT PRIMARY KEY, vendor_id TEXT, vendor_name TEXT,"
    " canonical_name TEXT, category TEXT, tier INTEGER)",
    "CREATE TABLE aliases (alias_norm TEXT, entity_id TEXT, strength TEXT, PRIMARY KEY (alias_norm, entity_id))",
    "CREATE TABLE vendor_aliases (alias_norm TEXT PRIMARY KEY, vendor_id TEXT)",
    "CREATE TABLE postings (token TEXT, alias_norm TEXT, PRIMARY KEY (token, alias_norm))",
    "CREATE TABLE idf (token TEXT PRIMARY KEY, idf REAL)",
    "CREATE TABLE synonyms (term TEXT PRIMARY KEY, concept_id TEXT NOT NULL)",
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
    db.executemany("INSERT INTO synonyms VALUES (?, ?)", tables.synonyms.items())


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
            synonyms=dict(db.execute("SELECT term, concept_id FROM synonyms ORDER BY 1")),
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
