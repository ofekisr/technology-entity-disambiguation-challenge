import json
import shutil
from pathlib import Path

import pytest

from src.cli import main
from src.constants import DATA_DIR


@pytest.fixture()
def data_dir(tmp_path: Path) -> Path:
    return Path(shutil.copytree(DATA_DIR, tmp_path / "data"))


def _run(argv: list[str], capsys: pytest.CaptureFixture[str]) -> tuple[int, str]:
    code = main(argv)
    return code, capsys.readouterr().out


def test_resolve_prints_resolution(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code, out = _run(["resolve", "AWS", "--snapshot", str(tmp_path / "s.sqlite")], capsys)
    assert code == 0
    assert json.loads(out)["status"] == "resolved"


def test_build_reports_version_and_size(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code, out = _run(["build", "--out", str(tmp_path / "s.sqlite")], capsys)
    report = json.loads(out)
    assert code == 0
    assert {"index_version", "entities", "aliases", "rss_mb"} <= report.keys()


def test_validate_seed_is_clean(capsys: pytest.CaptureFixture[str]) -> None:
    assert _run(["validate"], capsys)[0] == 0


def test_add_alias_is_idempotent(data_dir: Path, capsys: pytest.CaptureFixture[str]) -> None:
    argv = ["add-alias", "aws/eks", "Elastic K8s", "--data-dir", str(data_dir), "--reason", "test"]
    _run(argv, capsys)
    code, out = _run(argv, capsys)
    rows = (data_dir / "aliases.csv").read_text().count("Elastic K8s")
    assert (code, rows, out.strip()) == (0, 1, "unchanged")


def test_add_alias_rejects_unknown_entity(data_dir: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert _run(["add-alias", "nope/nope", "X Y", "--data-dir", str(data_dir)], capsys)[0] == 1
