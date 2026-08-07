from pathlib import Path

import pytest
from click.testing import CliRunner, Result
from pytest_httpserver import HTTPServer

from cg.cli.base import base
from cg.constants.constants import Workflow
from tests.integration.utils import (
    IntegrationTestPaths,
    expect_to_get_all_analyses_to_deliver_from_trailblazer,
)


@pytest.mark.xdist_group(name="integration")
@pytest.mark.integration
def test_deliver_all_available(httpserver: HTTPServer, test_run_paths: IntegrationTestPaths):
    cli_runner = CliRunner()

    # GIVEN a config file with valid database URIs and directories
    config_path: Path = test_run_paths.cg_config_file

    # GIVEN that Trailblazer has analyses ready for delivery
    expect_to_get_all_analyses_to_deliver_from_trailblazer(
        trailblazer_server=httpserver,
        exclude_workflows=[
            Workflow.MICROSALT,
            Workflow.TAXPROFILER,
            Workflow.DEMULTIPLEX,
            Workflow.RSYNC,
        ],
    )

    # WHEN running deliver all available
    result: Result = cli_runner.invoke(
        base,
        [
            "--config",
            config_path.as_posix(),
            "deliver",
            "all-available",
        ],
        catch_exceptions=False,
    )

    # THEN the delivery was successful
    assert result.exit_code == 0
