import pytest
from hypothesis import given
from hypothesis import strategies as st

from src.normalize import case_signals, normalize, split_camel, tokens

names = st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126), max_size=40)
VERSION_SUFFIXES = (" 2.14", " v7", " 10.0.1")


def test_version_tokens_are_dropped() -> None:
    assert normalize("Apache Log4j 2.14") == "apache log4j"


def test_v_prefixed_version_with_dots_is_dropped() -> None:
    assert normalize("V.0") == normalize(normalize("V.0")) == ""


def test_bare_integers_are_kept() -> None:
    assert normalize("Microsoft 365") == "microsoft 365"
    assert normalize("7-Zip") == "7 zip"


def test_symbol_tokens_stay_distinct() -> None:
    assert [normalize(name) for name in ("C++", "C#", "C", ".NET")] == ["c++", "c#", "c", ".net"]


def test_separators_split_tokens() -> None:
    assert tokens("F5-NGINX (AEM)") == ("f5", "nginx", "aem")


@given(names)
def test_idempotent(name: str) -> None:
    assert normalize(normalize(name)) == normalize(name)


@given(names)
def test_casing_invariant(name: str) -> None:
    assert normalize(name.upper()) == normalize(name.lower())


@given(names, st.sampled_from([".", ",", "!", ";"]))
def test_trailing_punctuation_invariant(name: str, mark: str) -> None:
    assert normalize(name + mark) == normalize(name)


@given(names, st.sampled_from(VERSION_SUFFIXES))
def test_version_suffix_invariant(name: str, suffix: str) -> None:
    assert normalize(name + suffix) == normalize(name)


@pytest.mark.parametrize(("raw", "split"), [("RedHat", "Red Hat"), ("IISServer", "IIS Server"), ("log4j", "log4j"), ("AWS", "AWS")])
def test_split_camel_breaks_words_at_inner_capitals(raw: str, split: str) -> None:
    assert split_camel(raw) == split


def test_all_caps_words_long_enough_to_be_typo_corrected_are_read_as_acronyms() -> None:
    assert case_signals("Jira PAAS on AWS", "jira paas on aws").acronyms == frozenset({"paas"})


def test_camel_split_is_empty_when_it_changes_nothing() -> None:
    assert case_signals("redhat", "redhat").split_text == ""
