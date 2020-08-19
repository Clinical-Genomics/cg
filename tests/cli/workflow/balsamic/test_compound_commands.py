from pathlib import Path
import json
import logging
import pytest

from cg.cli.workflow.balsamic.base import start, store, start_available, store_available

EXIT_SUCCESS = 0


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
    # THEN command should NOT execute successfully
    assert result.exit_code == EXIT_SUCCESS
    assert case_id in caplog.text


def test_store(tmpdir_factory, cli_runner, balsamic_context: dict, caplog):
    pass


def test_start_available(tmpdir_factory, cli_runner, balsamic_context: dict, caplog):
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
    caplog.set_level(logging.INFO)
    # GIVEN CASE ID of sample where read counts pass threshold
    case_id_success = "balsamic_case_wgs_single"
    # Ensure the config is mocked to run compound command
    Path.mkdir(
        Path(balsamic_context["BalsamicAnalysisAPI"].get_config_path(case_id_success)).parent,
        exist_ok=True,
    )
    Path(balsamic_context["BalsamicAnalysisAPI"].get_config_path(case_id_success)).touch(
        exist_ok=True
    )
    #Ensure case was successfully picked up by start-available and status set to running
    result = cli_runner.invoke(start_available, ["--dry-run"], obj=balsamic_context)
    assert result.exit_code == EXIT_SUCCESS
    assert case_id_success in caplog.text
    assert balsamic_context["BalsamicAnalysisAPI"].store.family(case_id_success).action == "running"


    balsamic_context["BalsamicAnalysisAPI"].housekeeper_api = real_housekeeper_api
    # WHEN running command
    result = cli_runner.invoke(store_available, ["--dry-run"], obj=balsamic_context)
    assert result.exit_code == EXIT_SUCCESS
    # THEN command runs successfully
    assert case_id_success in caplog.text
    # THEN bundle added successfully and action set to None
    assert balsamic_context["BalsamicAnalysisAPI"].store.family(case_id_success).action == None
    # THEN case has analyses
    assert balsamic_context["BalsamicAnalysisAPI"].store.family(case_id_success).analyses
    # THEN bundle exists in Housekeeper
    assert balsamic_context["BalsamicAnalysisAPI"].housekeeper_api.bundle(case_id_success)
