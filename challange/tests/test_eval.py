import json

import pytest

from src.cli import main
from src.constants import DATA_DIR, Status
from src.alias_sources import DEFAULT_ALIAS_SOURCES
from src.eval import alias_budget, build_gold_set, evaluate, load_hand_cases, without_alias
from src.models import load_sources
from src.resolver import Resolver
from src.tables import Tables

MIN_GOLD_CASES = 150
MIN_PARAPHRASE_CASES = 6
HAND_GOLD = DATA_DIR / "gold.jsonl"
REPORT_KEYS = {"coverage", "f1", "ambiguous_rate", "p50_ms", "p99_ms", "cost_per_1m_usd", "sweep", "reliability", "ece"}


@pytest.fixture(scope="module")
def report(tables: Tables) -> dict[str, object]:
    return evaluate(load_sources(DATA_DIR), tables)


@pytest.fixture(scope="module")
def budget(tables: Tables) -> dict[str, object]:
    return alias_budget(load_sources(DATA_DIR), tables)


def test_gold_set_size(tables: Tables) -> None:
    assert len(build_gold_set(load_sources(DATA_DIR), tables)) >= MIN_GOLD_CASES


def test_hand_gold_measures_paraphrases() -> None:
    kinds = [case.kind for case in load_hand_cases(HAND_GOLD)]
    assert kinds.count("paraphrase") >= MIN_PARAPHRASE_CASES


def test_hard_negatives_never_resolve_to_a_wrong_id(resolver: Resolver) -> None:
    for case in load_hand_cases(HAND_GOLD):
        result = resolver.resolve(case.input)
        if case.kind == "hard-negative" and result.status is Status.RESOLVED:
            assert result.id == case.expected_id, case.input


def test_precision_gate(report: dict[str, object], tables: Tables) -> None:
    assert report["precision_on_resolved"] >= tables.thresholds.precision_target


def test_report_has_all_metrics(report: dict[str, object]) -> None:
    assert REPORT_KEYS <= report.keys()


def test_without_alias_removes_it_everywhere(tables: Tables) -> None:
    reduced = without_alias(tables, "azure sentinel")
    assert "azure sentinel" not in reduced.aliases
    assert all("azure sentinel" not in found for found in reduced.postings.values())


def test_alias_budget_drops_each_source_once(budget: dict[str, object]) -> None:
    ablation = budget["ablation"]
    assert [row["source"] for row in ablation] == [type(source).__name__ for source in DEFAULT_ALIAS_SOURCES]
    assert all(row["alias_keys_lost"] > 0 for row in ablation)


def test_alias_curve_grows_coverage_with_aliases_per_entity(budget: dict[str, object]) -> None:
    curve = budget["curve"]
    assert curve[-1]["aliases_per_entity"] > curve[0]["aliases_per_entity"]
    assert curve[-1]["coverage"] >= curve[0]["coverage"]


def test_cli_eval_prints_report(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["eval"]) == 0
    printed = json.loads(capsys.readouterr().out)
    assert printed["gate_passed"] is True and {"ablation", "curve"} <= printed["alias_budget"].keys()
