"""This script tests the run cli command"""
import logging
from pathlib import Path

from cg.cli.workflow.balsamic.base import run

EXIT_SUCCESS = 0


def test_without_options(cli_runner, balsamic_context: dict):
    """Test command without case_id argument"""
    # GIVEN no case_id
    # WHEN dry running without anything specified
    result = cli_runner.invoke(run, obj=balsamic_context)
    # THEN command should NOT execute successfully
    assert result.exit_code != EXIT_SUCCESS
    # THEN command should mention argument
    assert "Missing argument" in result.output


def test_with_missing_case(cli_runner, balsamic_context: dict, caplog):
    """Test command with invalid case to start with"""
    caplog.set_level(logging.ERROR)
    # GIVEN case_id not in database
    case_id = "soberelephant"
    assert not balsamic_context["BalsamicAnalysisAPI"].store.family(case_id)
    # WHEN running
    result = cli_runner.invoke(run, [case_id], obj=balsamic_context)
    # THEN command should NOT successfully call the command it creates
    assert result.exit_code != EXIT_SUCCESS
    # THEN ERROR log should be printed containing invalid case_id
    assert case_id in caplog.text
    assert "not found" in caplog.text


def test_without_samples(cli_runner, balsamic_context: dict, caplog):
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
    assert "0" in caplog.text


def test_without_config(cli_runner, balsamic_context: dict, caplog):
    """Test command with case_id and no config file"""
    caplog.set_level(logging.ERROR)
    # GIVEN case-id
    case_id = "balsamic_case_wgs_single"
    # WHEN dry running with dry specified
    result = cli_runner.invoke(run, [case_id, "--dry-run"], obj=balsamic_context)
    # THEN command should NOT execute successfully
    assert result.exit_code != EXIT_SUCCESS
    # THEN warning should be printed that no config file is found
    assert "No config file found" in caplog.text


def test_with_config(tmpdir_factory, cli_runner, balsamic_context: dict, caplog):
    """Test command with case_id and config file"""
    caplog.set_level(logging.INFO)
    # GIVEN case-id
    case_id = "balsamic_case_wgs_single"
    # WHEN ensuring case config exists where it should be stored
    Path.mkdir(
        Path(balsamic_context["BalsamicAnalysisAPI"].get_config_path(case_id)).parent, exist_ok=True
    )
    Path(balsamic_context["BalsamicAnalysisAPI"].get_config_path(case_id)).touch(exist_ok=True)
    # WHEN dry running with dry specified
    result = cli_runner.invoke(run, [case_id, "--dry-run"], obj=balsamic_context)
    # THEN command should NOT execute successfully
    assert result.exit_code == EXIT_SUCCESS
    # THEN warning should be printed that no config file is found
    assert "balsamic" in caplog.text


def test_run_analysis(cli_runner, balsamic_context: dict, caplog):
    """Test command with run-analysis option"""
    caplog.set_level(logging.INFO)
    # GIVEN case-id
    case_id = "balsamic_case_wgs_single"
    # WHEN ensuring case config exists where it should be stored
    Path.mkdir(
        Path(balsamic_context["BalsamicAnalysisAPI"].get_config_path(case_id)).parent, exist_ok=True
    )
    Path(balsamic_context["BalsamicAnalysisAPI"].get_config_path(case_id)).touch(exist_ok=True)
    # WHEN dry running with run analysis option specified
    result = cli_runner.invoke(run, [case_id, "--dry-run", "--run-analysis"], obj=balsamic_context)
    # THEN command should execute successfully
    assert result.exit_code == EXIT_SUCCESS
    # THEN dry-print should include the option
    assert "--run-analysis" in caplog.text


def test_analysis_type_qc(cli_runner, balsamic_context: dict, caplog):
    """Test command with analysis-type qc option"""
    caplog.set_level(logging.INFO)
    # GIVEN case-id
    case_id = "balsamic_case_wgs_single"
    # WHEN ensuring case config exists where it should be stored
    Path.mkdir(
        Path(balsamic_context["BalsamicAnalysisAPI"].get_config_path(case_id)).parent, exist_ok=True
    )
    Path(balsamic_context["BalsamicAnalysisAPI"].get_config_path(case_id)).touch(exist_ok=True)
    # WHEN dry running with analysis type qc option specified
    result = cli_runner.invoke(
        run, [case_id, "--dry-run", "--analysis-type", "qc"], obj=balsamic_context
    )
    # THEN command should execute successfully
    assert result.exit_code == EXIT_SUCCESS
    # THEN dry-print should include the option
    assert "--analysis-type" in caplog.text
    assert "qc" in caplog.text


def test_priority_custom(cli_runner, balsamic_context: dict, caplog):
    """Test command with priority option"""
    caplog.set_level(logging.INFO)
    # GIVEN valid case-id
    case_id = "balsamic_case_wgs_single"
    option_key = "--priority"
    option_value = "high"
    # WHEN ensuring case config exists where it should be stored
    Path.mkdir(
        Path(balsamic_context["BalsamicAnalysisAPI"].get_config_path(case_id)).parent, exist_ok=True
    )
    Path(balsamic_context["BalsamicAnalysisAPI"].get_config_path(case_id)).touch(exist_ok=True)
    # WHEN dry running with option specified
    result = cli_runner.invoke(
        run, [case_id, "--dry-run", option_key, option_value], obj=balsamic_context
    )
    # THEN command should execute successfully
    assert result.exit_code == EXIT_SUCCESS
    # THEN dry-print should include the the option-value
    assert "--qos" in caplog.text
    assert option_value in caplog.text


def test_priority_clinical(cli_runner, balsamic_context: dict, caplog):
    """Test command with case_id set to default NORMAL priority, when priority is not set manually"""
    caplog.set_level(logging.INFO)
    # GIVEN valid case-id
    case_id = "balsamic_case_wgs_single"
    option_value = "normal"
    # WHEN ensuring case config exists where it should be stored
    Path.mkdir(
        Path(balsamic_context["BalsamicAnalysisAPI"].get_config_path(case_id)).parent, exist_ok=True
    )
    Path(balsamic_context["BalsamicAnalysisAPI"].get_config_path(case_id)).touch(exist_ok=True)
    # WHEN dry running with option specified
    result = cli_runner.invoke(run, [case_id, "--dry-run"], obj=balsamic_context)
    # THEN command should execute successfully
    assert result.exit_code == EXIT_SUCCESS
    # THEN dry-print should include the the option-value
    assert "--qos" in caplog.text
    assert option_value in caplog.text


def test_run_wes_application(cli_runner, balsamic_context: dict, caplog):
    """Test command with case_id that has WES application set in statusdb"""
    caplog.set_level(logging.INFO)
    # GIVEN valid case-id
    case_id = "balsamic_case_wes_tumor"
    # WHEN ensuring case config exists where it should be stored
    Path.mkdir(
        Path(balsamic_context["BalsamicAnalysisAPI"].get_config_path(case_id)).parent, exist_ok=True
    )
    Path(balsamic_context["BalsamicAnalysisAPI"].get_config_path(case_id)).touch(exist_ok=True)
    # WHEN dry running with option specified
    result = cli_runner.invoke(run, [case_id, "--dry-run"], obj=balsamic_context)
    # THEN command should execute successfully
    assert result.exit_code == EXIT_SUCCESS
    # THEN dry-print should show option disabling mutect in balsamic
    assert "--disable-variant-caller mutect" in caplog.text
