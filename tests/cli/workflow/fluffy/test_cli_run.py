from unittest.mock import PropertyMock, create_autospec

from click.testing import CliRunner

from cg.cli.workflow.fluffy.base import run
from cg.constants import EXIT_SUCCESS
from cg.meta.workflow.fluffy import FluffyAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.store.store import Store


def test_cli_run_dry(
    cli_runner: CliRunner, fluffy_case_id_existing: str, fluffy_context: CGConfig, caplog
):
    caplog.set_level("INFO")

    # GIVEN a case_id that does exist in database

    # WHEN running command in dry-run mode
    result = cli_runner.invoke(run, [fluffy_case_id_existing, "--dry-run"], obj=fluffy_context)

    # THEN command terminates successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN log informs about process running
    assert "Running command" in caplog.text


def test_cli_run_dry_no_case(
    cli_runner: CliRunner,
    fluffy_case_id_non_existing: str,
    fluffy_context: CGConfig,
    caplog,
):
    caplog.set_level("ERROR")

    # GIVEN a case_id that does NOT exist in database

    # WHEN running command in dry-run mode
    result = cli_runner.invoke(run, [fluffy_case_id_non_existing, "--dry-run"], obj=fluffy_context)

    # THEN command does not terminate successfully
    assert result.exit_code != EXIT_SUCCESS

    # THEN logging informs about the case_id not existing
    assert fluffy_case_id_non_existing in caplog.text
    assert "could not be found" in caplog.text


def test_cli_run(
    cli_runner: CliRunner, fluffy_case_id_existing: str, fluffy_context: CGConfig, caplog
):
    caplog.set_level("INFO")

    # GIVEN a case_id that does exist in database

    # WHEN running command
    result = cli_runner.invoke(run, [fluffy_case_id_existing], obj=fluffy_context)

    # THEN command terminates successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN log informs about process running
    assert "Running command" in caplog.text


def test_calls_on_analysis_started(cli_runner: CliRunner, fluffy_context: CGConfig):
    # GIVEN an instance of the FluffyAnalysisAPI has been setup
    analysis_api: FluffyAnalysisAPI = create_autospec(
        FluffyAnalysisAPI, status_db=PropertyMock(return_value=create_autospec(Store))
    )
    fluffy_context.meta_apis["analysis_api"] = analysis_api
    case_id = "some_case_id"

    # WHEN successfully invoking the run command
    cli_runner.invoke(run, [case_id], obj=fluffy_context)

    # THEN the on_analysis_started function has been called
    analysis_api.on_analysis_started.assert_called_with(case_id)
