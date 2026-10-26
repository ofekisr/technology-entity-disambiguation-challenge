import math
from collections import defaultdict

from src.catalog import Catalog, Scored
from src.matchers import Query
from src.models import Filters, Hints
from src.tables import Tables
from src.typos import EXACT_QUALITY, TypoCorrector

WeightedTokens = dict[str, float]


class FuzzyAlias:
    def __init__(self, tables: Tables, catalog: Catalog, typos: TypoCorrector) -> None:
        self.tables = tables
        self.catalog = catalog
        self.typos = typos
        self._unknown_idf = math.log1p(len({a for aliases in tables.postings.values() for a in aliases}))

    def match(self, query: Query) -> Scored:
        tokens = query.text.split()
        vendor_id, residue = self.decompose(tokens)
        hints = query.hints
        if vendor_id and hints.vendor is None:
            hints = Hints(vendor=vendor_id, category=hints.category)
        corrections = self.typos.corrections(tokens, query.case.acronyms)
        weighted = dict(corrections.get(token, (token, EXACT_QUALITY)) for token in tokens)
        required = {corrections.get(token, (token, EXACT_QUALITY))[0] for token in residue} if vendor_id else set()
        scores = self._candidate_scores(weighted, required, query.filters)
        top = sorted(scores.items(), key=lambda item: (-item[1], item[0]))[: self.tables.thresholds.top_k]
        return [self.catalog.boosted(score, entity_id, hints) for entity_id, score in top]

    def decompose(self, tokens: list[str]) -> tuple[str | None, list[str]]:
        for size in range(len(tokens), 0, -1):
            vendor_id = self.tables.vendor_aliases.get(" ".join(tokens[:size]))
            if vendor_id:
                return vendor_id, tokens[size:]
        return None, tokens

    def _candidate_scores(self, weighted: WeightedTokens, required: set[str], filters: Filters) -> dict[str, float]:
        scores: dict[str, float] = defaultdict(float)
        for alias_norm in sorted({a for token in weighted for a in self.tables.postings.get(token, ())}):
            alias_tokens = set(alias_norm.split())
            if required and not required & alias_tokens:
                continue
            score = self.jaccard(weighted, alias_tokens)
            for hit in self.tables.aliases[alias_norm]:
                if self.catalog.passes(hit.entity_id, filters):
                    scores[hit.entity_id] = max(scores[hit.entity_id], score)
        return scores

    def jaccard(self, weighted: WeightedTokens, alias_tokens: set[str]) -> float:
        common = sum(self.idf(token) * weighted[token] for token in sorted(weighted) if token in alias_tokens)
        union = sum(self.idf(token) for token in sorted(set(weighted) | alias_tokens))
        return common / union if union else 0.0

    def idf(self, token: str) -> float:
        return self.tables.idf.get(token, self._unknown_idf)
