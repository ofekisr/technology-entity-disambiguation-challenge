import csv
from datetime import datetime
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field

from src.constants import NO_CONFIDENCE, Status, Strength

ID_PATTERN = r"^[a-z0-9][a-z0-9_.+-]*/([a-z0-9][a-z0-9_.+-]*|\*)$"
SLUG_PATTERN = r"^[a-z0-9][a-z0-9_.+-]*$"


class Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class CategoryLeaf(Frozen):
    id: str = Field(pattern=SLUG_PATTERN)
    label: str
    group: str


class VendorRow(Frozen):
    vendor_id: str = Field(pattern=SLUG_PATTERN)
    name: str
    parent_vendor_id: str | None = None
    flagship_entity_id: str | None = Field(default=None, pattern=ID_PATTERN)
    aliases: tuple[str, ...] = ()


class EntityRow(Frozen):
    id: str = Field(pattern=ID_PATTERN)
    vendor_id: str = Field(pattern=SLUG_PATTERN)
    product: str
    category: str
    tier: int = 3
    cpe: str | None = None


class AliasRow(Frozen):
    alias: str = Field(min_length=1)
    entity_id: str = Field(pattern=ID_PATTERN)
    strength: Strength = Strength.STRONG
    source: str = "manual"
    actor: str = "seed"
    added_at: datetime | None = None
    reason: str = ""
    evidence_url: str = ""


class Hints(Frozen):
    vendor: str | None = None
    category: str | None = None


class Filters(Frozen):
    vendors: tuple[str, ...] = ()
    categories: tuple[str, ...] = ()
    include_uncategorized: bool = True


class Alternative(Frozen):
    id: str
    canonical_name: str
    confidence: float


class Resolution(Frozen):
    id: str | None
    canonical_name: str | None
    vendor: str | None
    category: str | None
    confidence: float
    status: Status
    alternatives: tuple[Alternative, ...] = ()
    index_version: str

    @classmethod
    def no_match(cls, index_version: str) -> "Resolution":
        return cls(
            id=None,
            canonical_name=None,
            vendor=None,
            category=None,
            confidence=NO_CONFIDENCE,
            status=Status.NO_MATCH,
            index_version=index_version,
        )


class Thresholds(Frozen):
    t_high: float
    t_low: float
    margin: float
    top_k: int
    hint_bonus: float
    precision_target: float
    coverage_target: float


class Sources(Frozen):
    categories: tuple[CategoryLeaf, ...]
    vendors: tuple[VendorRow, ...]
    entities: tuple[EntityRow, ...]
    aliases: tuple[AliasRow, ...]
    thresholds: Thresholds


def load_categories(path: Path) -> tuple[CategoryLeaf, ...]:
    groups: dict[str, dict[str, str]] = yaml.safe_load(path.read_text())
    return tuple(
        CategoryLeaf(id=leaf_id, label=label, group=group)
        for group, leaves in groups.items()
        for leaf_id, label in leaves.items()
    )


def load_vendors(path: Path) -> tuple[VendorRow, ...]:
    with path.open(newline="") as handle:
        return tuple(_vendor_row(row) for row in csv.DictReader(handle))


def _vendor_row(row: dict[str, str]) -> VendorRow:
    return VendorRow(
        vendor_id=row["vendor_id"],
        name=row["name"],
        parent_vendor_id=row["parent_vendor_id"] or None,
        flagship_entity_id=row["flagship_entity_id"] or None,
        aliases=tuple(alias for alias in row["aliases"].split("|") if alias),
    )


def load_entities(path: Path) -> tuple[EntityRow, ...]:
    lines = path.read_text().splitlines()
    return tuple(EntityRow.model_validate_json(line) for line in lines if line.strip())


def load_aliases(path: Path) -> tuple[AliasRow, ...]:
    with path.open(newline="") as handle:
        return tuple(AliasRow.model_validate(_drop_empty(row)) for row in csv.DictReader(handle))


def _drop_empty(row: dict[str, str]) -> dict[str, str]:
    return {key: value for key, value in row.items() if value != ""}


def load_sources(data_dir: Path) -> Sources:
    return Sources(
        categories=load_categories(data_dir / "categories.yaml"),
        vendors=load_vendors(data_dir / "vendors.csv"),
        entities=load_entities(data_dir / "entities.jsonl"),
        aliases=load_aliases(data_dir / "aliases.csv"),
        thresholds=Thresholds.model_validate(yaml.safe_load((data_dir / "thresholds.yaml").read_text())),
    )
