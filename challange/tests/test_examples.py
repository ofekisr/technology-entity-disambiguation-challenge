import json
from collections import Counter
from pathlib import Path

import pytest

from src.constants import DATA_DIR, FULL_CONFIDENCE
from src.eval import load_hand_cases
from src.examples import CASES, GROUPS, Json, Tracer, build_cases, embed_in_guide, write_json, write_markdown
from src.tables import Tables

MIN_PER_GROUP = 2
MAX_PER_GROUP = 6


@pytest.fixture(scope="module")
def cases(tables: Tables) -> list[Json]:
    return build_cases(Tracer(tables))


def test_every_case_is_traced_and_none_fails(cases: list[Json]) -> None:
    assert [case["input"] for case in cases if case["verdict"] == "fail"] == []


def test_every_group_shows_a_few_cases(cases: list[Json]) -> None:
    sizes = Counter(str(case["group"]) for case in cases)
    assert set(sizes) == set(GROUPS)
    assert all(MIN_PER_GROUP <= size <= MAX_PER_GROUP for size in sizes.values()), sizes


def test_no_case_repeats(cases: list[Json]) -> None:
    keys = [(str(case["input"]).lower(), json.dumps(case["hints"]), json.dumps(case["filters"])) for case in cases]
    assert len(keys) == len(set(keys))


def test_expectations_agree_with_gold() -> None:
    gold = {row.input: (row.expected_status.value, row.expected_id) for row in load_hand_cases(DATA_DIR / "gold.jsonl")}
    plain = [case for case in CASES if case.input in gold and not case.hints and not case.filters]
    assert [case.input for case in plain if gold[case.input] != (case.expected_status, case.expected_id)] == []


def test_trace_explains_each_resolved_answer(cases: list[Json]) -> None:
    for case in cases:
        result, decision = case["result"], case["decision"]
        if result["status"] == "resolved":
            assert (decision["top"], decision["top_raw"]) == (result["id"], result["confidence"]), case["input"]


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
