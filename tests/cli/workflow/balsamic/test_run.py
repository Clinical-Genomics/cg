"""This script tests the run cli command"""

import logging
from pathlib import Path
from unittest.mock import PropertyMock, create_autospec

from _pytest.logging import LogCaptureFixture
from click.testing import CliRunner, Result

from cg.cli.workflow.balsamic.base import run
from cg.constants import EXIT_SUCCESS
from cg.constants.priority import SlurmQos
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.store.store import Store
from tests.typed_mock import TypedMock, create_typed_mock


def test_without_options(cli_runner: CliRunner, balsamic_context: CGConfig):
    """Test command without case_id argument"""
    # GIVEN no case_id
    # WHEN dry running without anything specified
    result = cli_runner.invoke(run, obj=balsamic_context)
    # THEN command should NOT execute successfully
    assert result.exit_code != EXIT_SUCCESS
    # THEN command should mention argument
    assert "Missing argument" in result.output


def test_with_missing_case(cli_runner: CliRunner, balsamic_context: CGConfig, caplog):
    """Test command with invalid case to start with"""
    caplog.set_level(logging.ERROR)
    # GIVEN case_id not in database
    case_id = "soberelephant"
    assert not balsamic_context.status_db.get_case_by_internal_id(internal_id=case_id)
    # WHEN running
    result = cli_runner.invoke(run, [case_id], obj=balsamic_context)
    # THEN command should NOT successfully call the command it creates
    assert result.exit_code != EXIT_SUCCESS
    # THEN ERROR log should be printed containing invalid case_id
    assert case_id in caplog.text
    assert "could not be found" in caplog.text


def test_without_samples(cli_runner: CliRunner, balsamic_context: CGConfig, caplog):
    """Test command with case_id and no samples"""
    caplog.set_level(logging.ERROR)
    # GIVEN case-id
    case_id = "no_sample_case"
    # WHEN dry running with dry specified
    result = cli_runner.invoke(run, [case_id, "--dry-run"], obj=balsamic_context)
    # THEN command should NOT execute successfully
    assert result.exit_code != EXIT_SUCCESS
    # THEN warning should be printed that no config file is found
    assert case_id in caplog.text
    assert "no samples" in caplog.text


def test_without_config(cli_runner: CliRunner, balsamic_context: CGConfig, caplog):
    """Test command with case_id and no config file"""
    caplog.set_level(logging.ERROR)
    # GIVEN case-id
    case_id = "balsamic_case_wgs_single"
    # WHEN dry running with dry specified
    result = cli_runner.invoke(run, [case_id], obj=balsamic_context)
    # THEN command should NOT execute successfully
    assert result.exit_code != EXIT_SUCCESS
    # THEN warning should be printed that no config file is found
    assert "No config file found" in caplog.text


def test_with_config(tmpdir_factory, cli_runner: CliRunner, balsamic_context: CGConfig, caplog):
    """Test command with case_id and config file"""
    caplog.set_level(logging.INFO)
    # GIVEN case-id
    case_id = "balsamic_case_wgs_single"
    # WHEN ensuring case config exists where it should be stored
    Path.mkdir(
        Path(balsamic_context.meta_apis["analysis_api"].get_case_config_path(case_id)).parent,
        exist_ok=True,
    )
    Path(balsamic_context.meta_apis["analysis_api"].get_case_config_path(case_id)).touch(
        exist_ok=True
    )
    # WHEN dry running with dry specified
    result = cli_runner.invoke(run, [case_id, "--dry-run"], obj=balsamic_context)
    # THEN command should NOT execute successfully
    assert result.exit_code == EXIT_SUCCESS
    # THEN warning should be printed that no config file is found
    assert "balsamic" in caplog.text


def test_run_analysis(cli_runner: CliRunner, balsamic_context: CGConfig, caplog):
    """Test command with dry run option"""
    caplog.set_level(logging.INFO)
    # GIVEN case-id
    case_id = "balsamic_case_wgs_single"
    # WHEN ensuring case config exists where it should be stored
    Path.mkdir(
        Path(balsamic_context.meta_apis["analysis_api"].get_case_config_path(case_id)).parent,
        exist_ok=True,
    )
    Path(balsamic_context.meta_apis["analysis_api"].get_case_config_path(case_id)).touch(
        exist_ok=True
    )
    # WHEN dry running
    result = cli_runner.invoke(run, [case_id, "--dry-run"], obj=balsamic_context)
    # THEN command should execute successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN the partition flag should be included
    assert f"--headjob-partition {balsamic_context.balsamic.head_job_partition}" in caplog.text


def test_priority_custom(cli_runner: CliRunner, balsamic_context: CGConfig, caplog):
    """Test command with priority option"""
    caplog.set_level(logging.INFO)
    # GIVEN valid case-id
    case_id = "balsamic_case_wgs_single"
    qos_key = "--slurm-quality-of-service"
    qos_value = SlurmQos.HIGH
    # WHEN ensuring case config exists where it should be stored
    Path.mkdir(
        Path(balsamic_context.meta_apis["analysis_api"].get_case_config_path(case_id)).parent,
        exist_ok=True,
    )
    Path(balsamic_context.meta_apis["analysis_api"].get_case_config_path(case_id)).touch(
        exist_ok=True
    )
    # WHEN dry running with option specified
    result = cli_runner.invoke(
        run, [case_id, "--dry-run", qos_key, qos_value], obj=balsamic_context
    )
    # THEN command should execute successfully
    assert result.exit_code == EXIT_SUCCESS
    # THEN dry run should include the the priority value
    assert "--qos" in caplog.text
    assert qos_value in caplog.text


def test_priority_clinical(cli_runner: CliRunner, balsamic_context: CGConfig, caplog):
    """Test command with case_id set to default NORMAL priority, when priority is not set manually"""
    caplog.set_level(logging.INFO)

    # GIVEN valid case-id
    case_id = "balsamic_case_wgs_single"
    priority_value = SlurmQos.NORMAL

    # WHEN ensuring case config exists where it should be stored
    Path.mkdir(
        Path(balsamic_context.meta_apis["analysis_api"].get_case_config_path(case_id)).parent,
        exist_ok=True,
    )
    Path(balsamic_context.meta_apis["analysis_api"].get_case_config_path(case_id)).touch(
        exist_ok=True
    )

    # WHEN dry running with option specified
    result = cli_runner.invoke(run, [case_id, "--dry-run"], obj=balsamic_context)

    # THEN command should execute successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN dry run should include the the priority value
    assert "--qos" in caplog.text
    assert priority_value in caplog.text


def test_calls_on_analysis_started(cli_runner: CliRunner, balsamic_context: CGConfig):
    # GIVEN an instance of the BalsamicAnalysisAPI has been setup
    analysis_api: TypedMock[BalsamicAnalysisAPI] = create_typed_mock(
        BalsamicAnalysisAPI, status_db=PropertyMock(return_value=create_autospec(Store))
    )
    balsamic_context.meta_apis["analysis_api"] = analysis_api.as_type
    case_id = "some_balsamic_case_id"

    # WHEN successfully invoking the run command
    cli_runner.invoke(run, [case_id], obj=balsamic_context)

    # THEN the on_analysis_started function has been called
    analysis_api.as_mock.on_analysis_started.assert_called_with(case_id)


def test_workflow_profile_option(
    cli_runner: CliRunner,
    balsamic_context: CGConfig,
    caplog: LogCaptureFixture,
    tmp_path: Path,
):
    """Test run command with workflow-profile option."""
    caplog.set_level(logging.INFO)

    # GIVEN valid case-id
    case_id = "balsamic_case_wgs_single"

    # GIVEN that the case config file exists where it should be stored
    Path.mkdir(
        Path(balsamic_context.meta_apis["analysis_api"].get_case_config_path(case_id)).parent,
        exist_ok=True,
    )
    Path(balsamic_context.meta_apis["analysis_api"].get_case_config_path(case_id)).touch(
        exist_ok=True
    )
    config_path = Path(balsamic_context.meta_apis["analysis_api"].get_case_config_path(case_id))
    Path.mkdir(config_path.parent, exist_ok=True)
    config_path.touch(exist_ok=True)

    # GIVEN that the workflow-profile path exists
    workflow_profile = Path(tmp_path, "workflow_profile")
    workflow_profile.mkdir(parents=True, exist_ok=True)

    # WHEN dry running with the workflow-profile option specified
    result: Result = cli_runner.invoke(
        run,
        [
            case_id,
            "--dry-run",
            "--workflow-profile",
            workflow_profile.as_posix(),
        ],
        obj=balsamic_context,
    )

    # THEN command should execute successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN the workflow-profile option should be included in the run command
    assert f"--workflow-profile {workflow_profile.as_posix()}" in caplog.text
