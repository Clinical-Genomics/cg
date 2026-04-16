"""Tests CLI common methods to create the case config for NF analyses."""

import logging

import pytest
from click import BaseCommand
from click.testing import CliRunner, Result
from pytest_mock import MockerFixture

from cg.cli.workflow.nallo.base import config_case as nallo_config_case
from cg.cli.workflow.raredisease.base import config_case as raredisease_config_case
from cg.cli.workflow.rnafusion.base import config_case as rnafusion_config_case
from cg.cli.workflow.taxprofiler.base import config_case as taxprofiler_config_case
from cg.cli.workflow.tomte.base import config_case as tomte_config_case
from cg.constants import EXIT_SUCCESS
from cg.models.cg_config import CGConfig
from cg.services.analysis_starter.configurator.implementations.nextflow import NextflowConfigurator

LOG = logging.getLogger(__name__)


@pytest.mark.parametrize(
    "case_config_command",
    [
        nallo_config_case,
        raredisease_config_case,
        rnafusion_config_case,
        taxprofiler_config_case,
        tomte_config_case,
    ],
    ids=["Nallo", "raredisease", "RNAFUSION", "Taxprofiler", "Tomte"],
)
def test_nextflow_case_config(
    case_config_command: BaseCommand,
    cli_runner: CliRunner,
    cg_context: CGConfig,
    mocker: MockerFixture,
):
    # GIVEN a case id and a Nextflow configurator
    case_id: str = "some_case_id"
    config_mock = mocker.patch.object(NextflowConfigurator, "configure")

    # WHEN running the dev-config-case CLI command
    result: Result = cli_runner.invoke(case_config_command, [case_id], obj=cg_context)

    # THEN the configurator should have been called with the specified case id
    config_mock.assert_called_once_with(case_id=case_id)

    # THEN the command should have executed without fail
    assert result.exit_code == EXIT_SUCCESS
