"""This file groups all tests related to microsalt start creation"""

from pathlib import Path
from unittest.mock import create_autospec

from click.testing import CliRunner
from pytest_mock import MockerFixture

from cg.cli.workflow.microsalt.base import run
from cg.constants import Workflow
from cg.exc import CaseNotConfiguredError
from cg.models.cg_config import CGConfig
from cg.services.analysis_starter.configurator.models.microsalt import MicrosaltCaseConfig
from cg.services.analysis_starter.submitters.subprocess.submitter import SubprocessSubmitter
from cg.services.analysis_starter.tracker.tracker import Tracker
from cg.store.models import Case, Sample
from cg.store.store import Store


def test_run_raises_error_if_not_configured(
    cli_runner: CliRunner, cg_context: CGConfig, mocker: MockerFixture
):
    # GIVEN a case to run
    case_id = "some_case_id"

    # GIVEN that the case has a workflow and no ongoing analysis
    mocker.patch.object(Tracker, "ensure_analysis_not_ongoing", return_value=None)
    mock_case = create_autospec(Case)
    sample = create_autospec(Sample)
    mock_case.samples = [sample]
    mocker.patch.object(Store, "get_case_by_internal_id", return_value=mock_case)

    # GIVEN that the config file does not exist

    # WHEN running the case
    result = cli_runner.invoke(run, [case_id], obj=cg_context)

    # THEN an error should be raised
    assert isinstance(result.exception, CaseNotConfiguredError)


def test_run_tracks_case(cli_runner: CliRunner, cg_context: CGConfig, mocker: MockerFixture):
    # GIVEN a case to run
    case_id = "some_case_id"

    # GIVEN that the case has a workflow and no ongoing analysis _and_ is configured

    # GIVEN that the case is submitted successfully
    mocker.patch.object(Store, "update_case_action")
    mock_case = create_autospec(Case)
    mock_case.data_analysis = Workflow.MICROSALT
    mock_case.samples = [create_autospec(Sample), create_autospec(Sample)]
    mocker.patch.object(Store, "get_case_by_internal_id", return_value=mock_case)
    mocker.patch.object(Tracker, "ensure_analysis_not_ongoing", return_value=None)
    mocker.patch.object(Path, "exists", return_value=True)
    mocker.patch.object(SubprocessSubmitter, "submit", return_value=None)
    track_mock = mocker.patch.object(Tracker, "track")

    # WHEN running the case
    cli_runner.invoke(run, [case_id], obj=cg_context)

    # THEN the progress should be tracked
    microsalt_config = cg_context.microsalt
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
