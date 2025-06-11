"""This file groups all tests related to microsalt start creation"""

import logging
from pathlib import Path
from unittest.mock import PropertyMock, create_autospec

from click.testing import CliRunner
from pytest_mock import MockerFixture

from cg.cli.workflow.microsalt.base import dev_run, run
from cg.constants import Workflow
from cg.exc import CaseNotConfiguredError
from cg.meta.workflow.microsalt import MicrosaltAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.services.analysis_starter.configurator.models.microsalt import MicrosaltCaseConfig
from cg.services.analysis_starter.submitters.subprocess.submitter import SubprocessSubmitter
from cg.services.analysis_starter.tracker.tracker import Tracker
from cg.store.store import Store

EXIT_SUCCESS = 0


def test_no_arguments(cli_runner: CliRunner, base_context: CGConfig):
    """Test command without any options"""

    # GIVEN

    # WHEN dry running without anything specified
    result = cli_runner.invoke(run, obj=base_context)

    # THEN command should mention missing arguments
    assert result.exit_code != EXIT_SUCCESS


def test_dry_arguments(cli_runner: CliRunner, base_context: CGConfig, ticket_id, caplog):
    """Test command dry"""

    # GIVEN
    caplog.set_level(logging.INFO)

    # WHEN dry running without anything specified
    result = cli_runner.invoke(run, [ticket_id, "-t", "--dry-run"], obj=base_context)

    # THEN command should mention missing arguments
    assert result.exit_code == EXIT_SUCCESS
    assert "Running command" in caplog.text


def test_calls_on_analysis_started(cli_runner: CliRunner, base_context: CGConfig):
    # GIVEN an instance of the MicrosaltAnalysisAPI has been setup
    analysis_api: MicrosaltAnalysisAPI = create_autospec(
        MicrosaltAnalysisAPI,
        status_db=PropertyMock(
            return_value=create_autospec(Store),
        ),
    )
    base_context.meta_apis["analysis_api"] = analysis_api

    # GIVEN a case can be retrieved from the analysis api
    case_id = "some_case_id"
    analysis_api.resolve_case_sample_id = lambda sample, ticket, unique_id: (case_id, None)

    # WHEN successfully invoking the run command
    cli_runner.invoke(run, [case_id], obj=base_context)

    # THEN the on_analysis_started function has been called with the found case_id
    analysis_api.on_analysis_started.assert_called_with(case_id)


def test_run_raises_error_if_not_configured(
    cli_runner: CliRunner, base_context: CGConfig, mocker: MockerFixture
):
    # GIVEN a case to run
    case_id = "some_case_id"

    # GIVEN that the case has a workflow and no ongoing analysis
    mocker.patch.object(Store, "get_case_workflow", return_value=Workflow.MICROSALT)
    mocker.patch.object(Tracker, "ensure_analysis_not_ongoing", return_value=None)

    # GIVEN that the config file does not exist

    # WHEN running the case
    result = cli_runner.invoke(dev_run, [case_id], obj=base_context)

    # THEN an error should be raised
    assert isinstance(result.exception, CaseNotConfiguredError)


def test_run_tracks_case(cli_runner: CliRunner, base_context: CGConfig, mocker: MockerFixture):
    # GIVEN a case to run
    case_id = "some_case_id"

    # GIVEN that the case has a workflow and no ongoing analysis _and_ is configured

    # GIVEN that the case is submitted successfully
    mocker.patch.object(Store, "get_case_workflow", return_value=Workflow.MICROSALT)
    mocker.patch.object(Store, "update_case_action")
    mocker.patch.object(Tracker, "ensure_analysis_not_ongoing", return_value=None)
    mocker.patch.object(Path, "exists", return_value=True)
    mocker.patch.object(SubprocessSubmitter, "submit", return_value=None)
    track_mock = mocker.patch.object(Tracker, "track")

    # WHEN running the case
    cli_runner.invoke(dev_run, [case_id], obj=base_context)

    # THEN the progress should be tracked
    microsalt_config = base_context.microsalt
    expected_config_file = Path(microsalt_config.queries_path, case_id).with_suffix(".json")
    expected_fastq_dir = Path(microsalt_config.root, "fastq", case_id)
    expected_case_config = MicrosaltCaseConfig(
        binary=microsalt_config.binary_path,
        case_id=case_id,
        conda_binary=microsalt_config.conda_binary,
        config_file=expected_config_file.as_posix(),
        environment=microsalt_config.conda_env,
        fastq_directory=expected_fastq_dir.as_posix(),
    )
    track_mock.assert_called_once_with(case_config=expected_case_config, tower_workflow_id=None)
