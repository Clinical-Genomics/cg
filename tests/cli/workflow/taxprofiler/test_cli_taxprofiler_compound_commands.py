import logging

from _pytest.logging import LogCaptureFixture
from click.testing import CliRunner

from cg.apps.hermes.hermes_api import HermesApi
from cg.apps.hermes.models import CGDeliverables
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.cli.workflow.taxprofiler.base import (
    taxprofiler,
)
from cg.constants import EXIT_SUCCESS
from cg.meta.workflow.taxprofiler import TaxprofilerAnalysisAPI
from cg.models.cg_config import CGConfig


def test_taxprofiler_no_args(cli_runner: CliRunner, taxprofiler_context: CGConfig):
    """Test to see that running BALSAMIC without options prints help and doesn't result in an error."""
    # GIVEN no arguments or options besides the command call

    # WHEN running command
    result = cli_runner.invoke(taxprofiler, [], obj=taxprofiler_context)

    # THEN command runs successfully
    print(result.output)

    assert result.exit_code == EXIT_SUCCESS

    # THEN help should be printed
    assert "help" in result.output
