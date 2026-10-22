import json

import pytest

from src.build import Tables
from src.cli import main
from src.constants import DATA_DIR
from src.eval import build_gold_set, evaluate, without_alias
from src.models import load_sources

MIN_GOLD_CASES = 150
REPORT_KEYS = {"coverage", "f1", "ambiguous_rate", "p50_ms", "p99_ms", "cost_per_1m_usd", "sweep", "reliability", "ece"}


@pytest.fixture(scope="module")
def report(tables: Tables) -> dict[str, object]:
    return evaluate(load_sources(DATA_DIR), tables)


def test_gold_set_size(tables: Tables) -> None:
    assert len(build_gold_set(load_sources(DATA_DIR), tables)) >= MIN_GOLD_CASES


def test_precision_gate(report: dict[str, object], tables: Tables) -> None:
    assert report["precision_on_resolved"] >= tables.thresholds.precision_target


def test_report_has_all_metrics(report: dict[str, object]) -> None:
    assert REPORT_KEYS <= report.keys()


def test_without_alias_removes_it_everywhere(tables: Tables) -> None:
    reduced = without_alias(tables, "azure sentinel")
    assert "azure sentinel" not in reduced.aliases
    assert all("azure sentinel" not in found for found in reduced.postings.values())


def test_cli_eval_prints_report(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["eval"]) == 0
    assert json.loads(capsys.readouterr().out)["gate_passed"] is True
