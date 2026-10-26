import os
from functools import lru_cache
from pathlib import Path

from src.build import build_tables
from src.catalog import Catalog
from src.constants import DATA_DIR, DEFAULT_SNAPSHOT, LRU_MAXSIZE, Status
from src.decide import Decider
from src.fuzzy import FuzzyAlias
from src.matchers import ExactAlias, FirstHit, JoinedWords, Matcher, Query, SynonymRewrite, WithoutNumbers
from src.models import Filters, Hints, Resolution, load_sources
from src.normalize import normalize
from src.ports import InMemoryLedger, InMemoryReviewQueue, LedgerKey, ResponseLedger, ReviewQueue
from src.snapshot import load_snapshot, write_snapshot
from src.tables import Tables
from src.typos import TypoCorrector

SNAPSHOT_ENV = "IDX_SNAPSHOT"


def default_matcher(tables: Tables) -> Matcher:
    catalog = Catalog(tables)
    exact = ExactAlias(tables, catalog)
    fuzzy = FuzzyAlias(tables, catalog, TypoCorrector(tables.idf))
    exact_tiers = (exact, JoinedWords(exact), WithoutNumbers(exact, catalog))
    by_meaning = SynonymRewrite(FirstHit((*exact_tiers, fuzzy)), tables.synonyms, tables.idf)
    return FirstHit((*exact_tiers, by_meaning))


class Resolver:
    def __init__(
        self,
        tables: Tables,
        ledger: ResponseLedger | None = None,
        review_queue: ReviewQueue | None = None,
        matcher: Matcher | None = None,
    ) -> None:
        self.tables = tables
        self.ledger = ledger if ledger is not None else InMemoryLedger()
        self.review_queue = review_queue if review_queue is not None else InMemoryReviewQueue()
        self.matcher = matcher if matcher is not None else default_matcher(tables)
        self.decider = Decider(tables)
        self._cached = lru_cache(maxsize=LRU_MAXSIZE)(self._resolve_normalized)

    def resolve(self, name: str, *, hints: Hints | None = None, filters: Filters | None = None) -> Resolution:
        return self._cached(normalize(name), self.canonical_hints(hints or Hints()), canonical_filters(filters))

    def canonical_hints(self, hints: Hints) -> Hints:
        if hints.vendor is None:
            return hints
        vendor_id = self.tables.vendor_aliases.get(normalize(hints.vendor), hints.vendor)
        return Hints(vendor=vendor_id, category=hints.category)

    def _resolve_normalized(self, input_norm: str, hints: Hints, filters: Filters) -> Resolution:
        key = LedgerKey(input_norm, hints, filters, self.tables.index_version)
        recorded = self.ledger.get(key)
        if recorded is not None:
            return recorded
        result = self._compute(Query(input_norm, hints, filters))
        self.ledger.record(key, result)
        if result.status is Status.NO_MATCH and input_norm:
            self.review_queue.enqueue(input_norm, self.tables.index_version)
        return result

    def _compute(self, query: Query) -> Resolution:
        if not query.text:
            return Resolution.no_match(self.tables.index_version)
        return self.decider.decide(self.matcher.match(query))


def canonical_filters(filters: Filters | None) -> Filters:
    chosen = filters or Filters()
    return chosen.model_copy(update={"vendors": tuple(sorted(set(chosen.vendors))),
                                     "categories": tuple(sorted(set(chosen.categories)))})


def snapshot_path() -> Path:
    return Path(os.environ.get(SNAPSHOT_ENV, DEFAULT_SNAPSHOT))


@lru_cache(maxsize=1)
def default_resolver() -> Resolver:
    path = snapshot_path()
    if not path.exists():
        write_snapshot(build_tables(load_sources(DATA_DIR)), path)
    return Resolver(load_snapshot(path))


def resolve(name: str, *, hints: Hints | None = None, filters: Filters | None = None) -> Resolution:
    return default_resolver().resolve(name, hints=hints, filters=filters)
