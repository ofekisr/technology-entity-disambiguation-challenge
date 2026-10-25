from src.tables import Tables
from src.typos import TypoCorrector


def test_at_most_two_typo_tokens_are_corrected(tables: Tables) -> None:
    found = TypoCorrector(tables.idf).corrections("crowdstrik falcn kuberntes".split())
    assert found == {"crowdstrik": ("crowdstrike", 1 - 1 / 10), "falcn": ("falcon", 1 - 1 / 5)}


def test_known_and_short_tokens_are_left_alone(tables: Tables) -> None:
    corrector = TypoCorrector(tables.idf)
    assert (corrector.correct("falcon"), corrector.correct("eks")) == (None, None)
