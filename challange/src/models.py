from datetime import datetime

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
