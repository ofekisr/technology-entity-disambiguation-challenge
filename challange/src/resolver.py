import math
import os
from collections import defaultdict
from functools import lru_cache
from pathlib import Path

from rapidfuzz.distance import Levenshtein

from src.build import EntityRecord, Tables, build_tables, load_snapshot, write_snapshot
from src.constants import (
    BASE_BY_STRENGTH,
    DATA_DIR,
    DEFAULT_SNAPSHOT,
    EXACT_ONLY_MAX_LEN,
    FULL_CONFIDENCE,
    LRU_MAXSIZE,
    MAX_ALTERNATIVES,
    MAX_TYPO_DISTANCE,
    STRENGTH_RANK,
    UNCATEGORIZED,
    Status,
    Strength,
)
from src.models import Alternative, Filters, Hints, Resolution, load_sources
from src.normalize import normalize
from src.ports import InMemoryLedger, InMemoryReviewQueue, LedgerKey, ResponseLedger, ReviewQueue

TRIGRAM = 3
EXACT_QUALITY = 1.0
SNAPSHOT_ENV = "IDX_SNAPSHOT"
STRONG_RANK = STRENGTH_RANK[Strength.STRONG]

Scored = list[tuple[float, str]]
WeightedTokens = dict[str, float]


def trigrams(token: str) -> set[str]:
    padded = f" {token} "
    return {padded[i : i + TRIGRAM] for i in range(len(padded) - TRIGRAM + 1)}


class Resolver:
    def __init__(
        self,
        tables: Tables,
        ledger: ResponseLedger | None = None,
        review_queue: ReviewQueue | None = None,
    ) -> None:
        self.tables = tables
        self.ledger = ledger if ledger is not None else InMemoryLedger()
        self.review_queue = review_queue if review_queue is not None else InMemoryReviewQueue()
        self._trigram_index = self._build_trigram_index()
        self._unknown_idf = math.log1p(len({a for aliases in tables.postings.values() for a in aliases}))
        self._cached = lru_cache(maxsize=LRU_MAXSIZE)(self._resolve_normalized)

    def resolve(self, name: str, *, hints: Hints | None = None, filters: Filters | None = None) -> Resolution:
        return self._cached(normalize(name), self._canonical_hints(hints or Hints()), filters or Filters())

    def _canonical_hints(self, hints: Hints) -> Hints:
        if hints.vendor is None:
            return hints
        vendor_id = self.tables.vendor_aliases.get(normalize(hints.vendor), hints.vendor)
        return Hints(vendor=vendor_id, category=hints.category)

    def _resolve_normalized(self, input_norm: str, hints: Hints, filters: Filters) -> Resolution:
        key = LedgerKey(input_norm, hints, filters, self.tables.index_version)
        recorded = self.ledger.get(key)
        if recorded is not None:
            return recorded
        result = self._compute(input_norm, hints, filters)
        self.ledger.record(key, result)
        if result.status is Status.NO_MATCH:
            self.review_queue.enqueue(input_norm, self.tables.index_version)
        return result

    def _compute(self, input_norm: str, hints: Hints, filters: Filters) -> Resolution:
        if not input_norm:
            return Resolution.no_match(self.tables.index_version)
        exact = self._exact(input_norm, hints, filters)
        if exact:
            return self._decide(exact)
        return self._decide(self._fuzzy(input_norm, hints, filters))

    def _exact(self, input_norm: str, hints: Hints, filters: Filters) -> Scored:
        hits = [hit for hit in self.tables.aliases.get(input_norm, ()) if self._passes(hit.entity_id, filters)]
        if len(hits) == 1 and STRENGTH_RANK[hits[0].strength] >= STRONG_RANK:
            return [(BASE_BY_STRENGTH[hits[0].strength], hits[0].entity_id)]
        return [(BASE_BY_STRENGTH[hit.strength] + self._bonus(hit.entity_id, hints), hit.entity_id) for hit in hits]

    def _fuzzy(self, input_norm: str, hints: Hints, filters: Filters) -> Scored:
        vendor_id, residue = self._decompose(input_norm.split())
        if vendor_id and hints.vendor is None:
            hints = Hints(vendor=vendor_id, category=hints.category)
        weighted = dict(self._correct(token) for token in input_norm.split())
        required = {self._correct(token)[0] for token in residue} if vendor_id else set()
        scores = self._candidate_scores(weighted, required, filters)
        top = sorted(scores.items(), key=lambda item: (-item[1], item[0]))[: self.tables.thresholds.top_k]
        return [(score + self._bonus(entity_id, hints), entity_id) for entity_id, score in top]

    def _decompose(self, tokens: list[str]) -> tuple[str | None, list[str]]:
        for size in range(len(tokens), 0, -1):
            vendor_id = self.tables.vendor_aliases.get(" ".join(tokens[:size]))
            if vendor_id:
                return vendor_id, tokens[size:]
        return None, tokens

    def _correct(self, token: str) -> tuple[str, float]:
        if token in self.tables.idf or len(token) <= EXACT_ONLY_MAX_LEN:
            return token, EXACT_QUALITY
        candidates = {match for gram in trigrams(token) for match in self._trigram_index.get(gram, ())}
        ranked = sorted((Levenshtein.distance(token, match), match) for match in candidates)
        if not ranked or ranked[0][0] > MAX_TYPO_DISTANCE:
            return token, EXACT_QUALITY
        distance, match = ranked[0]
        return match, EXACT_QUALITY - distance / max(len(token), len(match))

    def _candidate_scores(self, weighted: WeightedTokens, required: set[str], filters: Filters) -> dict[str, float]:
        scores: dict[str, float] = defaultdict(float)
        for alias_norm in sorted({a for token in weighted for a in self.tables.postings.get(token, ())}):
            alias_tokens = set(alias_norm.split())
            if required and not required & alias_tokens:
                continue
            score = self._jaccard(weighted, alias_tokens)
            for hit in self.tables.aliases[alias_norm]:
                if self._passes(hit.entity_id, filters):
                    scores[hit.entity_id] = max(scores[hit.entity_id], score)
        return scores

    def _jaccard(self, weighted: WeightedTokens, alias_tokens: set[str]) -> float:
        common = sum(self._idf(token) * quality for token, quality in weighted.items() if token in alias_tokens)
        union = sum(self._idf(token) for token in set(weighted) | alias_tokens)
        return common / union if union else 0.0

    def _idf(self, token: str) -> float:
        return self.tables.idf.get(token, self._unknown_idf)

    def _bonus(self, entity_id: str, hints: Hints) -> float:
        record = self.tables.entities[entity_id]
        matches = hints.vendor == record.vendor_id or hints.category == record.category
        return self.tables.thresholds.hint_bonus if matches else 0.0

    def _passes(self, entity_id: str, filters: Filters) -> bool:
        record = self.tables.entities[entity_id]
        vendor_ok = not filters.vendors or record.vendor_id in filters.vendors
        uncategorized_ok = filters.include_uncategorized and record.category == UNCATEGORIZED
        category_ok = not filters.categories or record.category in filters.categories or uncategorized_ok
        return vendor_ok and category_ok

    def _decide(self, scored: Scored) -> Resolution:
        ranked = sorted(scored, key=lambda item: (-item[0], item[1]))
        thresholds = self.tables.thresholds
        if not ranked or ranked[0][0] < thresholds.t_low:
            return Resolution.no_match(self.tables.index_version)
        top_score, top_id = ranked[0]
        margin = top_score - (ranked[1][0] if len(ranked) > 1 else 0.0)
        if top_score >= thresholds.t_high and margin >= thresholds.margin:
            return self._resolved(self.tables.entities[top_id], top_score)
        return self._ambiguous([item for item in ranked if item[0] >= thresholds.t_low])

    def _resolved(self, record: EntityRecord, score: float) -> Resolution:
        return Resolution(
            id=record.id,
            canonical_name=record.canonical_name,
            vendor=record.vendor_name,
            category=record.category,
            confidence=self._calibrate(score),
            status=Status.RESOLVED,
            index_version=self.tables.index_version,
        )

    def _ambiguous(self, ranked: Scored) -> Resolution:
        shown = ranked[:MAX_ALTERNATIVES]
        total = sum(score for score, _ in shown)
        alternatives = tuple(
            Alternative(id=entity_id, canonical_name=self.tables.entities[entity_id].canonical_name, confidence=round(score / total, 4))
            for score, entity_id in shown
        )
        empty = Resolution.no_match(self.tables.index_version)
        top = self._calibrate(shown[0][0])
        return empty.model_copy(update={"status": Status.AMBIGUOUS, "confidence": top, "alternatives": alternatives})

    def _calibrate(self, score: float) -> float:
        capped = min(score, FULL_CONFIDENCE)
        scale = next((s for low, high, s in self.tables.calibration if low <= capped < high), FULL_CONFIDENCE)
        return round(min(capped * scale, FULL_CONFIDENCE), 4)

    def _build_trigram_index(self) -> dict[str, tuple[str, ...]]:
        index: dict[str, set[str]] = defaultdict(set)
        for token in self.tables.idf:
            if len(token) > EXACT_ONLY_MAX_LEN:
                for gram in trigrams(token):
                    index[gram].add(token)
        return {gram: tuple(sorted(tokens)) for gram, tokens in index.items()}


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
