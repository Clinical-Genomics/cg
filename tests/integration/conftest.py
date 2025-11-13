from collections.abc import Generator
from pathlib import Path
from unittest.mock import create_autospec

import pytest
from housekeeper.store import database as hk_database
from housekeeper.store.store import Store as HousekeeperStore
from pytest import TempPathFactory

from cg.apps.tb.api import IDTokenCredentials
from cg.constants.constants import Workflow
from cg.store import database as cg_database
from cg.store.store import Store
from tests.integration.utils import IntegrationTestPaths, create_formatted_config


@pytest.fixture(autouse=True)
def current_workflow() -> Workflow:
    raise NotImplementedError("Please add a current_workflow fixture to your integration test")


@pytest.fixture(autouse=True)
def valid_google_token(mocker):
    mocker.patch.object(
        IDTokenCredentials,
        "from_service_account_file",
        return_value=create_autospec(IDTokenCredentials, token="some token"),
    )


@pytest.fixture(scope="session")
def httpserver_listen_address() -> tuple[str, int]:
    return ("localhost", 8888)


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
def test_run_paths(
    status_db_uri: str,
    housekeeper_db_uri: str,
    tmp_path_factory: TempPathFactory,
    current_workflow,
) -> IntegrationTestPaths:
    test_root_dir: Path = tmp_path_factory.mktemp(current_workflow)

    config_file_path: Path = create_formatted_config(
        status_db_uri=status_db_uri,
        housekeeper_db_uri=housekeeper_db_uri,
        test_root_dir=test_root_dir.as_posix(),
    )

    return IntegrationTestPaths(cg_config_file=config_file_path, test_root_dir=test_root_dir)
