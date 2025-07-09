"""This file groups all tests related to microSALT case config creation."""

from click.testing import CliRunner, Result
from pytest_mock import MockerFixture

from cg.cli.workflow.microsalt.base import config_case
from cg.constants import EXIT_SUCCESS
from cg.models.cg_config import CGConfig
from cg.services.analysis_starter.configurator.implementations.microsalt import (
    MicrosaltConfigurator,
)


def test_dev_case_config(cli_runner: CliRunner, cg_context: CGConfig, mocker: MockerFixture):

    # GIVEN a microSALT configurator
    config_mock = mocker.patch.object(MicrosaltConfigurator, "configure")

    # WHEN running the dev-config-case CLI command
    result: Result = cli_runner.invoke(config_case, ["some_case_id"], obj=cg_context)

    # THEN the configurator should have been called with the specified case id
    config_mock.assert_called_once_with(case_id="some_case_id")

    # THEN the command should have executed without fail
    assert result.exit_code == EXIT_SUCCESS
