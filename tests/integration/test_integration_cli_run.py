from unittest.mock import create_autospec

import pytest
from click.testing import CliRunner

from cg.apps.tb.api import IDTokenCredentials
from cg.cli.base import base
from cg.cli.workflow.microsalt.base import run
from cg.exc import CaseNotConfiguredError
from cg.models.cg_config import CGConfig
from cg.services.analysis_starter.tracker.tracker import Tracker
from cg.store.models import Case, Sample
from cg.store.store import Store


@pytest.mark.integration
def test_run_raises_error_if_not_configured(mocker):

    cli_runner = CliRunner()

    # GIVEN a case to run
    case_id = "some_case_id"

    mocker.patch.object(
        IDTokenCredentials,
        "from_service_account_file",
        return_value=create_autospec(IDTokenCredentials, token="some token"),
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

    assert result.exception.__context__ == "?"
    # THEN an error should be raised
    assert isinstance(result.exception, CaseNotConfiguredError)
