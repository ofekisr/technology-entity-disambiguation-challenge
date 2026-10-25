from dataclasses import dataclass, field

from src.constants import VENDOR_PRODUCT, Strength
from src.models import Thresholds
from src.normalize import tokens

AliasTriple = tuple[str, str, Strength]


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
    synonyms: dict[str, str]
    thresholds: Thresholds
    calibration: tuple[tuple[float, float, float], ...]
    index_version: str = field(default="")


def canonical_name(vendor_name: str, product: str) -> str:
    if tokens(product)[: len(tokens(vendor_name))] == tokens(vendor_name):
        return product
    return f"{vendor_name} {product}"


def vendor_entity_id(vendor_id: str) -> str:
    return f"{vendor_id}/{VENDOR_PRODUCT}"
