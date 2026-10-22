import pytest
from pydantic import ValidationError

from src.constants import Status, Strength
from src.models import AliasRow, EntityRow, Resolution


def test_entity_row_rejects_bad_id() -> None:
    with pytest.raises(ValidationError):
        EntityRow(id="AWS EKS", vendor_id="aws", product="EKS", category="cloud-service")


def test_alias_row_defaults_strong() -> None:
    row = AliasRow(alias="Amazon EKS", entity_id="aws/eks")
    assert row.strength is Strength.STRONG


def test_resolution_no_match_shape() -> None:
    result = Resolution.no_match("abc123")
    assert result.status is Status.NO_MATCH
    assert result.canonical_name is None
    assert result.confidence == 0
