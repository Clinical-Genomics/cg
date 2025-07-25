from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner, Result
from pytest_mock import MockerFixture

from cg.cli.workflow.microsalt.base import start, start_available
from cg.constants import EXIT_FAIL, EXIT_SUCCESS
from cg.models.cg_config import CGConfig
from cg.services.analysis_starter.service import AnalysisStarter


def test_start(cli_runner: CliRunner, cg_context: CGConfig, mocker: MockerFixture):
    # GIVEN a valid context and a case id
    case_id: str = "case_id"

    # GIVEN a mocked AnalysisStarter that simulates the start method
    service_call: MagicMock = mocker.patch.object(AnalysisStarter, "start")

    # WHEN running the start command
    result: Result = cli_runner.invoke(start, [case_id], obj=cg_context)

    # THEN the starter command should have been called with the specified case id
    service_call.assert_called_once_with(case_id)

    # THEN the command should have executed without fail
    assert result.exit_code == EXIT_SUCCESS


@pytest.mark.parametrize(
    "succeeds, exit_status",
    [
        (True, EXIT_SUCCESS),
        (False, EXIT_FAIL),
    ],
)
def test_start_available(
    cli_runner: CliRunner,
    cg_context: CGConfig,
    succeeds: bool,
    exit_status: int,
    mocker: MockerFixture,
):
    """
    Test that the start_available command succeeds when the starter succeeds and aborts otherwise.
    """
    # GIVEN a valid context

    # GIVEN a mocked AnalysisStarter that simulates the start_available method
    service_call: MagicMock = mocker.patch.object(
        AnalysisStarter, "start_available", return_value=succeeds
    )

    # WHEN running the start_available command
    result: Result = cli_runner.invoke(start_available, obj=cg_context)

    # THEN the starter command should have been called
    service_call.assert_called_once()

    # THEN the command should have executed as expected
    assert result.exit_code == exit_status
