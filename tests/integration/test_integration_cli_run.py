import traceback
from unittest.mock import create_autospec

import pytest
from click.testing import CliRunner
from pytest_httpserver import HTTPServer

from cg.apps.tb.api import IDTokenCredentials
from cg.cli.base import base
from cg.cli.workflow.microsalt.base import run
from cg.exc import CaseNotConfiguredError
from cg.services.analysis_starter.tracker.tracker import Tracker
from cg.store import database
from cg.store.database import Session
from cg.store.models import Case
from cg.store.store import Store


@pytest.fixture(autouse=True)
def valid_google_token(mocker):
    mocker.patch.object(
        IDTokenCredentials,
        "from_service_account_file",
        return_value=create_autospec(IDTokenCredentials, token="some token"),
    )


@pytest.fixture(scope="session")
def httpserver_listen_address():
    return ("localhost", 8888)


@pytest.fixture
def store() -> Store:
    database.initialize_database("sqlite:///file:cg?mode=memory&cache=shared&uri=true")
    database.create_all_tables()
    store = Store()
    return store


@pytest.mark.integration
def test_run_raises_error_if_not_configured(microsalt_store: Store, httpserver: HTTPServer):

    cli_runner = CliRunner()

    # GIVEN a case to run
    case_id = "microparakeet"

    # GIVEN trailblazer returns an analysis for the case that is not complete
    # TODO: should there even be an analysis at this stage?
    httpserver.expect_request("/trailblazer/get-latest-analysis").respond_with_json(
        {
            "id": "12345",
            "logged_at": "2025-07-30",
            "started_at": "2025-07-30",
            "completed_at": "",
            "out_dir": "/out/dir",
            "config_path": "/config/path",
        }
    )

    # GIVEN that the config file for a case does not exist

    # WHEN running the case
    result = cli_runner.invoke(
        base,
        [
            "--config",
            "tests/integration/config/cg-test.yaml",
            "workflow",
            "microsalt",
            "run",
            case_id,
        ],
    )

    traceback.print_exception(result.exception)

    # THEN an error should be raised
    assert isinstance(result.exception, CaseNotConfiguredError)

    # THEN the case should not be running
    case: Case | None = microsalt_store.get_case_by_internal_id(case_id)
    assert case and case.action == None
