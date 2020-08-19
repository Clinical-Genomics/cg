from pathlib import Path
import json
import logging
import pytest

from cg.cli.workflow.balsamic.base import balsamic, start, store, start_available, store_available

EXIT_SUCCESS = 0


def test_balsamic_no_args(cli_runner, balsamic_context: dict):
    result = cli_runner.invoke(balsamic, [], obj=balsamic_context)
    assert result.exit_code == EXIT_SUCCESS
    assert "balsamic" in result.output


def test_start(tmpdir_factory, cli_runner, balsamic_context: dict, caplog):
    caplog.set_level(logging.INFO)

    case_id = "balsamic_case_wgs_single"
    # WHEN ensuring case config exists where it should be stored
    Path.mkdir(
        Path(balsamic_context["BalsamicAnalysisAPI"].get_config_path(case_id)).parent, exist_ok=True
    )
    Path(balsamic_context["BalsamicAnalysisAPI"].get_config_path(case_id)).touch(exist_ok=True)
    # WHEN dry running with dry specified
    result = cli_runner.invoke(start, [case_id, "--dry-run"], obj=balsamic_context)
    # THEN command should execute successfully
    assert result.exit_code == EXIT_SUCCESS
    assert case_id in caplog.text


def test_store(
    tmpdir_factory,
    cli_runner,
    balsamic_context: dict,
    real_housekeeper_api,
    mock_config,
    mock_deliverable,
    mock_analysis_finish,
    caplog,
):
    """Test to ensure all parts of compound store command are executed given ideal conditions"""
    caplog.set_level(logging.INFO)
    # GIVEN case-id
    case_id = "balsamic_case_wgs_single"
    # Make sure nothing is currently stored in Housekeeper
    balsamic_context["BalsamicAnalysisAPI"].housekeeper_api = real_housekeeper_api
    # Make sure  analysis not alredy stored in ClinicalDB
    assert not balsamic_context["BalsamicAnalysisAPI"].store.family(case_id).analyses
    # WHEN running command
    result = cli_runner.invoke(store, [case_id, "--dry-run"], obj=balsamic_context)
    # THEN bundle should be successfully added to HK and STATUS
    assert result.exit_code == EXIT_SUCCESS
    assert "Analysis successfully stored in Housekeeper" in caplog.text
    assert "Analysis successfully stored in ClinicalDB" in caplog.text
    assert balsamic_context["BalsamicAnalysisAPI"].store.family(case_id).analyses
    assert balsamic_context["BalsamicAnalysisAPI"].housekeeper_api.bundle(case_id)


def test_start_available(tmpdir_factory, cli_runner, balsamic_context: dict, caplog):
    """Test to ensure all parts of compound start-availbale command are executed given ideal conditions
    Test that start-available picks up eligeble cases and does not pick up ineligeble ones"""
    caplog.set_level(logging.INFO)
    # GIVEN CASE ID of sample where read counts pass threshold
    case_id_success = "balsamic_case_wgs_paired"
    # GIVEN CASE ID where read counts did not pass the threshold
    case_id_fail = "balsamic_case_tgs_paired"
    # Ensure the config is mocked to run compound command
    Path.mkdir(
        Path(balsamic_context["BalsamicAnalysisAPI"].get_config_path(case_id_success)).parent,
        exist_ok=True,
    )
    Path(balsamic_context["BalsamicAnalysisAPI"].get_config_path(case_id_success)).touch(
        exist_ok=True
    )
    # WHEN running command
    result = cli_runner.invoke(start_available, ["--dry-run"], obj=balsamic_context)
    # THEN command runs successfully
    assert result.exit_code == EXIT_SUCCESS
    # THEN it should successfully identify the one case eligeble for auto-start
    assert case_id_success in caplog.text
    # THEN action of the case should be set to running
    assert balsamic_context["BalsamicAnalysisAPI"].store.family(case_id_success).action == "running"
    # THEN the ineligeble case should NOT be ran
    assert case_id_fail not in caplog.text
    # THEN action of the case should NOT be set to running
    assert balsamic_context["BalsamicAnalysisAPI"].store.family(case_id_fail).action == None


def test_store_available(
    tmpdir_factory,
    cli_runner,
    balsamic_context: dict,
    real_housekeeper_api,
    mock_config,
    mock_deliverable,
    mock_analysis_finish,
    caplog,
):
    """Test to ensure all parts of compound store-availbale command are executed given ideal conditions
    Test that sore-available picks up eligeble cases and does not pick up ineligeble ones"""
    caplog.set_level(logging.INFO)
    # GIVEN CASE ID of sample where read counts pass threshold
    case_id_success = "balsamic_case_wgs_single"
    # GIVEN CASE ID where analysis finish is not mocked
    case_id_fail = "balsamic_case_wgs_paired"
    # Ensure the config is mocked for fail case to run compound command
    Path.mkdir(
        Path(balsamic_context["BalsamicAnalysisAPI"].get_config_path(case_id_fail)).parent,
        exist_ok=True,
    )
    Path(balsamic_context["BalsamicAnalysisAPI"].get_config_path(case_id_fail)).touch(exist_ok=True)
    # Ensure case was successfully picked up by start-available and status set to running
    result = cli_runner.invoke(start_available, ["--dry-run"], obj=balsamic_context)
    assert result.exit_code == EXIT_SUCCESS
    assert case_id_success in caplog.text
    assert balsamic_context["BalsamicAnalysisAPI"].store.family(case_id_success).action == "running"

    balsamic_context["BalsamicAnalysisAPI"].housekeeper_api = real_housekeeper_api
    # WHEN running command
    result = cli_runner.invoke(store_available, ["--dry-run"], obj=balsamic_context)
    # THEN command runs successfully
    assert result.exit_code == EXIT_SUCCESS
    # THEN case id with analysis_finish gets picked up
    assert case_id_success in caplog.text
    # THEN bundle added successfully and action set to None
    assert balsamic_context["BalsamicAnalysisAPI"].store.family(case_id_success).action == None
    # THEN case id WITHOUT analysis_finish is still running
    assert balsamic_context["BalsamicAnalysisAPI"].store.family(case_id_fail).action == "running"
    # THEN case has analyses
    assert balsamic_context["BalsamicAnalysisAPI"].store.family(case_id_success).analyses
    # THEN bundle can be found in Housekeeper
    assert balsamic_context["BalsamicAnalysisAPI"].housekeeper_api.bundle(case_id_success)
