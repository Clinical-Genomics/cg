"""This script tests the run cli command"""
import logging
from pathlib import Path

from click.testing import CliRunner

from cg.cli.workflow.rnafusion.base import run
from cg.constants import EXIT_SUCCESS
from cg.constants.priority import SlurmQos
from cg.models.cg_config import CGConfig


def test_without_options(cli_runner: CliRunner, rnafusion_context: CGConfig):
    """Test command without case_id argument"""
    # GIVEN no case_id
    # WHEN dry running without anything specified
    result = cli_runner.invoke(run, obj=rnafusion_context)
    # THEN command should NOT execute successfully
    assert result.exit_code != EXIT_SUCCESS
    # THEN command should mention argument
    assert "Missing argument" in result.output


def test_with_missing_case(cli_runner: CliRunner, rnafusion_context: CGConfig, caplog):
    """Test command with invalid case to start with"""
    caplog.set_level(logging.ERROR)
    # GIVEN case_id not in database
    case_id = "soberelephant"
    assert not rnafusion_context.status_db.family(case_id)
    # WHEN running
    result = cli_runner.invoke(run, [case_id], obj=rnafusion_context)
    # THEN command should NOT successfully call the command it creates
    assert result.exit_code != EXIT_SUCCESS
    # THEN ERROR log should be printed containing invalid case_id
    assert case_id in caplog.text
    assert "could not be found" in caplog.text


def test_without_samples(cli_runner: CliRunner, rnafusion_context: CGConfig, caplog):
    """Test command with case_id and no samples"""
    caplog.set_level(logging.ERROR)
    # GIVEN case-id
    case_id = "no_sample_case"
    # WHEN dry running with dry specified
    result = cli_runner.invoke(run, [case_id, "--dry-run"], obj=rnafusion_context)
    # THEN command should NOT execute successfully
    assert result.exit_code != EXIT_SUCCESS
    # THEN warning should be printed that no config file is found
    assert case_id in caplog.text
    assert "no samples" in caplog.text


def test_without_config(cli_runner: CliRunner, rnafusion_context: CGConfig, caplog):
    """Test command with case_id and no config file"""
    caplog.set_level(logging.ERROR)
    # GIVEN case-id
    case_id = "rnafusion_case_enough_reads"
    # WHEN dry running with dry specified
    result = cli_runner.invoke(run, [case_id, "--dry-run"], obj=rnafusion_context)
    # THEN command should NOT execute successfully
    assert result.exit_code != EXIT_SUCCESS
    # THEN warning should be printed that no config file is found
    assert "No config file found" in caplog.text


def test_with_config(tmpdir_factory, cli_runner: CliRunner, rnafusion_context: CGConfig, caplog):
    """Test command with case_id and config file"""
    caplog.set_level(logging.INFO)
    # GIVEN case-id
    case_id = "rnafusion_case_enough_reads"
    # WHEN ensuring case config exists where it should be stored
    Path.mkdir(
        Path(rnafusion_context.meta_apis["analysis_api"].get_case_config_path(case_id)).parent,
        exist_ok=True,
    )
    Path(rnafusion_context.meta_apis["analysis_api"].get_case_config_path(case_id)).touch(
        exist_ok=True
    )
    # WHEN dry running with dry specified
    result = cli_runner.invoke(run, [case_id, "--dry-run"], obj=rnafusion_context)
    # THEN command should NOT execute successfully
    assert result.exit_code == EXIT_SUCCESS
