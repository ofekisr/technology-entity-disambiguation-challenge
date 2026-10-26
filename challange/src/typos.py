from collections import defaultdict

from rapidfuzz.distance import Levenshtein

from src.constants import EXACT_ONLY_MAX_LEN, MAX_TYPO_DISTANCE, MAX_TYPO_TOKENS, SHORT_TYPO_DISTANCE, SHORT_TYPO_TOKEN_LEN

TRIGRAM = 3
EXACT_QUALITY = 1.0

Correction = tuple[str, float]


def trigrams(token: str) -> set[str]:
    padded = f" {token} "
    return {padded[i : i + TRIGRAM] for i in range(len(padded) - TRIGRAM + 1)}


class TypoCorrector:
    def __init__(self, idf: dict[str, float]) -> None:
        self.vocabulary = idf
        self._index = _trigram_index(idf)

    def corrections(self, tokens: list[str], keep: frozenset[str] = frozenset()) -> dict[str, Correction]:
        found: dict[str, Correction] = {}
        for token in tokens:
            corrected = None if token in keep else self.correct(token)
            if corrected and len(found) < MAX_TYPO_TOKENS:
                found[token] = corrected
        return found

    def correct(self, token: str) -> Correction | None:
        if token in self.vocabulary or len(token) <= EXACT_ONLY_MAX_LEN:
            return None
        candidates = {match for gram in trigrams(token) for match in self._index.get(gram, ())}
        ranked = sorted((Levenshtein.distance(token, match), match) for match in candidates)
        if not ranked or ranked[0][0] > _max_distance(token):
            return None
        distance, match = ranked[0]
        return match, EXACT_QUALITY - distance / len(token)


def _trigram_index(vocabulary: dict[str, float]) -> dict[str, tuple[str, ...]]:
    index: dict[str, set[str]] = defaultdict(set)
    for token in vocabulary:
        if len(token) > EXACT_ONLY_MAX_LEN:
            for gram in trigrams(token):
                index[gram].add(token)
    return {gram: tuple(sorted(tokens)) for gram, tokens in index.items()}


def _max_distance(token: str) -> int:
    return SHORT_TYPO_DISTANCE if len(token) == SHORT_TYPO_TOKEN_LEN else MAX_TYPO_DISTANCE
