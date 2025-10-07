from collections.abc import Generator
from pathlib import Path
from typing import NamedTuple
from unittest.mock import create_autospec

import pytest
from housekeeper.store import database as hk_database
from housekeeper.store.store import Store as HousekeeperStore
from pytest import TempPathFactory
from pytest_httpserver import HTTPServer

from cg.apps.environ import environ_email
from cg.apps.tb.api import IDTokenCredentials
from cg.constants.constants import Workflow
from cg.constants.tb import AnalysisType
from cg.store import database as cg_database
from cg.store.models import Case
from cg.store.store import Store


class IntegrationTestPaths(NamedTuple):
    cg_config_file: Path
    test_root_dir: Path


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

    config_file_path = create_parsed_config(
        status_db_uri=status_db_uri,
        housekeeper_db_uri=housekeeper_db_uri,
        test_root_dir=test_root_dir.as_posix(),
    )

    return IntegrationTestPaths(cg_config_file=config_file_path, test_root_dir=test_root_dir)


def expect_to_add_pending_analysis_to_trailblazer(
    trailblazer_server: HTTPServer,
    case: Case,
    ticket_id: int,
    case_path: Path,
    config_path: Path,
    type: AnalysisType,
    workflow: Workflow,
):
    trailblazer_server.expect_request(
        "/trailblazer/add-pending-analysis",
        data=b'{"case_id": "%(case_id)s", "email": "%(email)s", "type": "%(type)s", '
        b'"config_path": "%(config_path)s",'
        b' "order_id": 1, "out_dir": "%(case_path)s/analysis", '
        b'"priority": "normal", "workflow": "%(workflow)s", "ticket": "%(ticket_id)s", '
        b'"workflow_manager": "slurm", "tower_workflow_id": null, "is_hidden": true}'
        % {
            b"email": environ_email().encode(),
            b"type": str(type).encode(),
            b"case_id": case.internal_id.encode(),
            b"ticket_id": str(ticket_id).encode(),
            b"case_path": str(case_path).encode(),
            b"config_path": str(config_path).encode(),
            b"workflow": str(workflow).upper().encode(),
        },
        method="POST",
    ).respond_with_json(
        {
            "id": "1",
            "logged_at": "",
            "started_at": "",
            "completed_at": "",
            "out_dir": "out/dir",
            "config_path": "config/path",
        }
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
