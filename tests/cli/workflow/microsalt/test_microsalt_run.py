"""This file groups all tests related to microsalt start creation"""

from pathlib import Path
from unittest import mock

from click.testing import CliRunner

from cg.cli.workflow.microsalt.base import run
from cg.constants import Workflow
from cg.exc import CaseNotConfiguredError
from cg.models.cg_config import CGConfig
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


def test_calls_on_analysis_started(cli_runner: CliRunner, base_context: CGConfig):
    # GIVEN a case to run
    case_id = "some_case_id"

    with (
        mock.patch.object(Store, "get_case_workflow", return_value=Workflow.MICROSALT),
        mock.patch.object(SubprocessSubmitter, "submit", return_value=None),
        mock.patch.object(Tracker, "ensure_analysis_not_ongoing", return_value=None),
        mock.patch.object(Tracker, "track") as run_mock,
    ):

        # WHEN successfully invoking the run command
        cli_runner.invoke(run, [case_id], obj=base_context)

    # THEN the on_analysis_started function has been called with the found case_id
    run_mock.assert_called_with(case_id=case_id, config_file=None)


def test_run_raises_error_if_not_configured(cli_runner: CliRunner, base_context: CGConfig):
    # GIVEN a case to run
    case_id = "some_case_id"

    # GIVEN that the case has a workflow and no ongoing analysis
    with (
        mock.patch.object(Store, "get_case_workflow", return_value=Workflow.MICROSALT),
        mock.patch.object(Tracker, "ensure_analysis_not_ongoing", return_value=None),
    ):

        # GIVEN that the config file does not exist

        # WHEN running the case
        result = cli_runner.invoke(run, [case_id], obj=base_context)

        # THEN an error should be raised
        assert isinstance(result.exception, CaseNotConfiguredError)


def test_run_tracks_case(cli_runner: CliRunner, base_context: CGConfig):
    # GIVEN a case to run
    case_id = "some_case_id"

    # GIVEN that the case has a workflow and no ongoing analysis _and_ is configured

    # GIVEN that the case is submitted successfully
    with (
        mock.patch.object(Store, "get_case_workflow", return_value=Workflow.MICROSALT),
        mock.patch.object(Tracker, "ensure_analysis_not_ongoing", return_value=None),
        mock.patch.object(Path, "exists", return_value=True),
        mock.patch.object(SubprocessSubmitter, "submit", return_value=None),
        mock.patch.object(Tracker, "track") as run_mock,
    ):

        # WHEN running the case
        cli_runner.invoke(run, [case_id], obj=base_context)

        # THEN the progress should be tracked
        run_mock.assert_called_once()
