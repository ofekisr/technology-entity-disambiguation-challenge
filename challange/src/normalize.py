import re
import unicodedata
from dataclasses import dataclass

from src.constants import EXACT_ONLY_MAX_LEN, SYMBOL_TOKENS

SEPARATORS = re.compile(r"[\s\-_/,;:()\[\]{}\"'!?&|*@<>=~`^\\]+")
VERSION_TOKEN = re.compile(r"^(v\d[\d.]*|\d+\.[\d.]*)$")
NON_TOKEN_CHARS = re.compile(r"[^a-z0-9+#.]")
CAMEL_BOUNDARY = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")


def tokens(name: str) -> tuple[str, ...]:
    folded = unicodedata.normalize("NFKC", name).casefold()
    cleaned = (_clean(raw) for raw in SEPARATORS.split(folded))
    return tuple(token for token in cleaned if token)


def normalize(name: str) -> str:
    return " ".join(tokens(name))


@dataclass(frozen=True)
class CaseSignals:
    split_text: str = ""
    acronyms: frozenset[str] = frozenset()


def split_camel(name: str) -> str:
    return CAMEL_BOUNDARY.sub(" ", name)


def case_signals(name: str, input_norm: str) -> CaseSignals:
    split = normalize(split_camel(name))
    return CaseSignals(split if split != input_norm else "", _acronyms(name))


def _acronyms(name: str) -> frozenset[str]:
    upper = (raw for raw in SEPARATORS.split(name) if raw.isupper())
    return frozenset(token for token in (_clean(raw.casefold()) for raw in upper) if len(token) > EXACT_ONLY_MAX_LEN)


def _clean(raw: str) -> str:
    trimmed = raw.rstrip(".")
    if trimmed in SYMBOL_TOKENS:
        return trimmed
    cleaned = NON_TOKEN_CHARS.sub("", trimmed).strip(".")
    joined = cleaned.replace(".", "")
    if VERSION_TOKEN.match(cleaned) or VERSION_TOKEN.match(joined):
        return ""
    return joined
