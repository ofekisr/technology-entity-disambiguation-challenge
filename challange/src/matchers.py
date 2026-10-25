from collections.abc import Iterator, Sequence
from dataclasses import dataclass, replace
from typing import Protocol

from src.catalog import Catalog, Scored
from src.constants import BASE_BY_STRENGTH, STRENGTH_RANK, Strength
from src.models import Filters, Hints
from src.tables import Tables

STRONG_RANK = STRENGTH_RANK[Strength.STRONG]
WEAK_BASE = BASE_BY_STRENGTH[Strength.WEAK]


@dataclass(frozen=True)
class Query:
    text: str
    hints: Hints
    filters: Filters


class Matcher(Protocol):
    def match(self, query: Query) -> Scored: ...


class ExactAlias:
    def __init__(self, tables: Tables, catalog: Catalog) -> None:
        self.tables = tables
        self.catalog = catalog

    def match(self, query: Query) -> Scored:
        hits = [hit for hit in self.tables.aliases.get(query.text, ()) if self.catalog.passes(hit.entity_id, query.filters)]
        if len(hits) == 1 and STRENGTH_RANK[hits[0].strength] >= STRONG_RANK:
            return [self.catalog.boosted(BASE_BY_STRENGTH[hits[0].strength], hits[0].entity_id, Hints())]
        return [self.catalog.boosted(BASE_BY_STRENGTH[hit.strength], hit.entity_id, query.hints) for hit in hits]


class JoinedWords:
    def __init__(self, exact: Matcher) -> None:
        self.exact = exact

    def match(self, query: Query) -> Scored:
        for variant in _joined_variants(query.text.split()):
            hits = self.exact.match(replace(query, text=variant))
            if hits:
                return hits
        return []


class WithoutNumbers:
    def __init__(self, exact: Matcher, catalog: Catalog) -> None:
        self.exact = exact
        self.catalog = catalog

    def match(self, query: Query) -> Scored:
        stripped = " ".join(token for token in query.text.split() if not token.isdigit())
        if not stripped or stripped == query.text:
            return []
        hits = self.exact.match(replace(query, text=stripped))
        return [self.catalog.boosted(min(raw, WEAK_BASE), entity_id, query.hints) for _, raw, entity_id in hits if not self.catalog.is_vendor(entity_id)]


class FirstHit:
    def __init__(self, matchers: Sequence[Matcher]) -> None:
        self.matchers = tuple(matchers)

    def match(self, query: Query) -> Scored:
        for matcher in self.matchers:
            hits = matcher.match(query)
            if hits:
                return hits
        return []


def _joined_variants(tokens: list[str]) -> Iterator[str]:
    for index in range(len(tokens) - 1):
        yield " ".join([*tokens[:index], tokens[index] + tokens[index + 1], *tokens[index + 2 :]])
