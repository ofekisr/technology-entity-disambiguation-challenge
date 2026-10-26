import re
import unicodedata

from src.constants import SYMBOL_TOKENS

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


def split_camel(name: str) -> str:
    return CAMEL_BOUNDARY.sub(" ", name)


def _clean(raw: str) -> str:
    trimmed = raw.rstrip(".")
    if trimmed in SYMBOL_TOKENS:
        return trimmed
    cleaned = NON_TOKEN_CHARS.sub("", trimmed).strip(".")
    joined = cleaned.replace(".", "")
    if VERSION_TOKEN.match(cleaned) or VERSION_TOKEN.match(joined):
        return ""
    return joined
