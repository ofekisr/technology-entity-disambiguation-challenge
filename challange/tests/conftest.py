import pytest

from src.build import build_tables
from src.constants import DATA_DIR
from src.models import load_sources
from src.resolver import Resolver
from src.tables import Tables


@pytest.fixture(scope="session")
def tables() -> Tables:
    return build_tables(load_sources(DATA_DIR))


@pytest.fixture()
def resolver(tables: Tables) -> Resolver:
    return Resolver(tables)
