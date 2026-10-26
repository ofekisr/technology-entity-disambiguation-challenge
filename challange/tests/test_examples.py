from pathlib import Path

import pytest

from src.constants import FULL_CONFIDENCE
from src.examples import Json, Tracer, build_cases, embed_in_guide, write_json, write_markdown
from src.tables import Tables

MIN_CASES = 60


@pytest.fixture(scope="module")
def cases(tables: Tables) -> list[Json]:
    return build_cases(Tracer(tables))


def test_every_case_is_traced_and_none_fails(cases: list[Json]) -> None:
    assert len(cases) >= MIN_CASES
    assert [case["input"] for case in cases if case["verdict"] == "fail"] == []


def test_trace_explains_each_resolved_answer(cases: list[Json]) -> None:
    for case in cases:
        result, decision = case["result"], case["decision"]
        if result["status"] == "resolved":
            assert decision["top"] == result["id"], case["input"]


def test_every_case_states_its_final_answer(cases: list[Json]) -> None:
    for case in cases:
        assert case["final"]["answer"].startswith(case["result"]["status"]), case["input"]
        assert 0.0 <= case["result"]["confidence"] <= FULL_CONFIDENCE


def test_rank_above_one_returns_the_raw_score_as_confidence(cases: list[Json]) -> None:
    lifted = next(case for case in cases if case["decision"].get("top_rank", 0.0) > FULL_CONFIDENCE)
    assert lifted["result"]["confidence"] == lifted["decision"]["top_raw"] <= FULL_CONFIDENCE
    assert "only ordered" in lifted["final"]["why"]


def test_markdown_and_guide_json_are_written(cases: list[Json], tables: Tables, tmp_path: Path) -> None:
    markdown = tmp_path / "examples.md"
    write_markdown(cases, tables, markdown)
    guide = tmp_path / "guide.html"
    guide.write_text('<script type="application/json" id="examples-data">STALE-DATA</script>')
    assert embed_in_guide(guide, write_json(cases, tables, tmp_path / "examples.json"))
    assert tables.index_version in markdown.read_text() and "STALE-DATA" not in guide.read_text()
