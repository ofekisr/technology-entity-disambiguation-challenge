from enum import StrEnum
from pathlib import Path
from typing import Final


class Status(StrEnum):
    RESOLVED = "resolved"
    AMBIGUOUS = "ambiguous"
    NO_MATCH = "no_match"


class Strength(StrEnum):
    CANONICAL = "canonical"
    STRONG = "strong"
    GENERATED = "generated"
    WEAK = "weak"


BASE_BY_STRENGTH: Final[dict[Strength, float]] = {
    Strength.CANONICAL: 1.0,
    Strength.STRONG: 0.97,
    Strength.GENERATED: 0.9,
    Strength.WEAK: 0.8,
}
STRENGTH_RANK: Final[dict[Strength, int]] = {
    Strength.CANONICAL: 3,
    Strength.STRONG: 2,
    Strength.GENERATED: 1,
    Strength.WEAK: 0,
}

MAX_TYPO_DISTANCE: Final = 2
EXACT_ONLY_MAX_LEN: Final = 3
MAX_ALTERNATIVES: Final = 5
LRU_MAXSIZE: Final = 10_000
CALIBRATION_BINS: Final = 10
NO_CONFIDENCE: Final = 0.0
FULL_CONFIDENCE: Final = 1.0

VENDOR_PRODUCT: Final = "*"
VENDOR_CATEGORY: Final = "vendor"
UNCATEGORIZED: Final = "uncategorized"
SYMBOL_TOKENS: Final = frozenset({"c++", "c#", "f#", ".net"})

DATA_DIR: Final = Path(__file__).parent / "data"
DEFAULT_SNAPSHOT: Final = Path(__file__).parent.parent / "build" / "index.sqlite"
