from pathlib import Path

from src.build import build_tables, load_snapshot, validate, write_snapshot
from src.constants import DATA_DIR, Strength
from src.models import AliasRow, Sources, VendorRow, load_sources


def _sources() -> Sources:
    return load_sources(DATA_DIR)


def _with_alias(sources: Sources, alias: str, entity_id: str) -> Sources:
    extra = AliasRow(alias=alias, entity_id=entity_id)
    return sources.model_copy(update={"aliases": (*sources.aliases, extra)})


def _targets(sources: Sources, alias: str) -> set[str]:
    return {hit.entity_id for hit in build_tables(sources).aliases[alias]}


def test_index_version_is_content_hash() -> None:
    sources = _sources()
    first, second = build_tables(sources), build_tables(sources)
    changed = build_tables(_with_alias(sources, "Elastic K8s", "aws/eks"))
    assert first.index_version == second.index_version
    assert first.index_version != changed.index_version


def test_generated_aliases() -> None:
    assert _targets(_sources(), "amazon eks") == {"aws/eks"}
    assert _targets(_sources(), "sentinel siem") == {"microsoft/sentinel"}


def test_generated_never_shadows_manual() -> None:
    assert _targets(_sources(), "microsoft copilot") == {"microsoft/copilot"}


def test_short_alias_is_weak() -> None:
    hits = build_tables(_sources()).aliases["eks"]
    assert [hit.strength for hit in hits] == [Strength.WEAK]


def test_validate_accepts_seed() -> None:
    sources = _sources()
    assert validate(sources, build_tables(sources)) == []


def test_validate_rejects_strong_alias_on_two_entities() -> None:
    sources = _with_alias(_sources(), "Azure Sentinel", "hashicorp/sentinel")
    assert any("azure sentinel" in error for error in validate(sources, build_tables(sources)))


def test_validate_rejects_vendor_cycle() -> None:
    sources = _sources()
    looped = [VendorRow(vendor_id="amazon", name="Amazon", parent_vendor_id="aws")]
    vendors = tuple(v for v in sources.vendors if v.vendor_id != "amazon") + tuple(looped)
    broken = sources.model_copy(update={"vendors": vendors})
    assert any("cycle" in error for error in validate(broken, build_tables(broken)))


def test_snapshot_round_trip(tmp_path: Path) -> None:
    tables = build_tables(_sources())
    path = tmp_path / "index.sqlite"
    write_snapshot(tables, path)
    assert load_snapshot(path) == tables
