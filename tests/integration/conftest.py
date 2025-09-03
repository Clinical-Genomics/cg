from collections.abc import Generator
from pathlib import Path

import pytest
from housekeeper.store import database as hk_database
from housekeeper.store.store import Store as HousekeeperStore
from pytest import TempPathFactory

from cg.store import database as cg_database
from cg.store.store import Store


@pytest.fixture
def status_db_uri() -> str:
    return "sqlite:///file:cg?mode=memory&cache=shared&uri=true"


@pytest.fixture
def housekeeper_db_uri() -> str:
    return "sqlite:///file:housekeeper?mode=memory&cache=shared&uri=true"


@pytest.fixture
def status_db(status_db_uri: str) -> Generator[Store, None, None]:
    cg_database.initialize_database(status_db_uri)
    cg_database.create_all_tables()
    store = Store()
    yield store
    cg_database.drop_all_tables()


@pytest.fixture
def housekeeper_db(
    housekeeper_db_uri: str, tmp_path_factory: TempPathFactory
) -> Generator[HousekeeperStore, None, None]:
    hk_database.initialize_database(housekeeper_db_uri)
    hk_database.create_all_tables()
    housekeeper_root: Path = tmp_path_factory.mktemp("housekeeper")
    store = HousekeeperStore(root=housekeeper_root.as_posix())
    yield store
    hk_database.drop_all_tables()


@pytest.fixture
def cg_config_file(
    status_db_uri: str, housekeeper_db_uri: str, tmp_path_factory: TempPathFactory
) -> Path:
    test_root_dir: Path = tmp_path_factory.mktemp("balsamic")

    return create_parsed_config(
        status_db_uri=status_db_uri,
        housekeeper_db_uri=housekeeper_db_uri,
        test_root_dir=test_root_dir.as_posix(),
    )


def create_parsed_config(status_db_uri: str, housekeeper_db_uri: str, test_root_dir: str):
    template_path = "tests/integration/config/cg-test.yaml"
    with open(template_path) as f:
        config_content = f.read()

    config_content = config_content.format(
        test_root_dir=test_root_dir,
        status_db_uri=status_db_uri,
        housekeeper_db_uri=housekeeper_db_uri,
    )

    config_path = Path(test_root_dir, "cg-config.yaml")
    with open(config_path, "w") as f:
        f.write(config_content)
    return config_path
