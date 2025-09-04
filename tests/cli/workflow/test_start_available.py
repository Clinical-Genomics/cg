from unittest.mock import MagicMock

import pytest
from click import BaseCommand
from click.testing import CliRunner, Result
from pytest_mock import MockerFixture

from cg.cli.workflow.microsalt.base import start_available as microsalt_start_available
from cg.cli.workflow.mip_dna.base import dev_start_available as mip_dna_start_available
from cg.cli.workflow.raredisease.base import dev_start_available as raredisease_start_available
from cg.cli.workflow.rnafusion.base import start_available as rnafusion_start_available
from cg.cli.workflow.taxprofiler.base import dev_start_available as taxprofiler_start_available
from cg.constants import EXIT_FAIL, EXIT_SUCCESS
from cg.models.cg_config import CGConfig
from cg.services.analysis_starter.service import AnalysisStarter


@pytest.mark.parametrize(
    "start_available_command",
    [
        raredisease_start_available,
        rnafusion_start_available,
        taxprofiler_start_available,
        mip_dna_start_available,
        microsalt_start_available,
    ],
    ids=["raredisease", "RNAFUSION", "Taxprofiler", "MIP-DNA", "microSALT"],
)
@pytest.mark.parametrize(
    "succeeds, exit_status",
    [
        (True, EXIT_SUCCESS),
        (False, EXIT_FAIL),
    ],
)
def test_start_available_calls_analysis_starter(
    start_available_command: BaseCommand,
    succeeds: bool,
    exit_status: int,
    cli_runner: CliRunner,
    cg_context: CGConfig,
    mocker: MockerFixture,
):
    """
    Test that the start_available command succeeds when the starter succeeds and aborts otherwise.
    """
    # GIVEN a sufficient context

    # GIVEN a mocked AnalysisStarter that simulates the start_available method
    analysis_starter_start_available: MagicMock = mocker.patch.object(
        AnalysisStarter, "start_available", return_value=succeeds
    )

    # WHEN running the start-available command
    result: Result = cli_runner.invoke(start_available_command, obj=cg_context)

    # THEN the analysis starter should have been called with the expected input
    analysis_starter_start_available.assert_called_once()

    # THEN the command should have executed without fail
    assert result.exit_code == exit_status
