from pathlib import Path
import logging

from cg.cli.workflow.balsamic.base import (
    balsamic,
    start,
    store,
    start_available,
    store_available,
)

EXIT_SUCCESS = 0


def test_balsamic_no_args(cli_runner, balsamic_context: dict):
    """Test to see that running BALSAMIC without options prints help and doesn't result in an error"""
    # GIVEN no arguments or options besides the command call

    # WHEN running command
    result = cli_runner.invoke(balsamic, [], obj=balsamic_context)

    # THEN command runs successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN help should be printed
    assert "help" in result.output


def test_start(cli_runner, balsamic_context: dict, mock_config, caplog):
    """Test to ensure all parts of start command will run successfully given ideal conditions"""
    caplog.set_level(logging.INFO)

    # GIVEN case id for which we created a config file
    case_id = "balsamic_case_wgs_single"

    # WHEN dry running with dry specified
    result = cli_runner.invoke(start, [case_id, "--dry-run"], obj=balsamic_context)

    # THEN command should execute successfully
    assert result.exit_code == EXIT_SUCCESS
    assert case_id in caplog.text


def test_store(
    cli_runner,
    balsamic_context: dict,
    real_housekeeper_api,
    mock_config,
    mock_deliverable,
    mock_analysis_finish,
    caplog,
):
    """Test to ensure all parts of store command are run successfully given ideal conditions"""
    caplog.set_level(logging.INFO)

    # GIVEN case-id for which we created a config file, deliverables file, and analysis_finish file
    case_id = "balsamic_case_wgs_single"

    # Set Housekeeper to an empty real Housekeeper store
    balsamic_context["BalsamicAnalysisAPI"].housekeeper_api = real_housekeeper_api

    # Make sure the bundle was not present in the store
    assert not balsamic_context["BalsamicAnalysisAPI"].housekeeper_api.bundle(case_id)

    # Make sure  analysis not already stored in ClinicalDB
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
    """Test to ensure all parts of compound start-available command are executed given ideal conditions
    Test that start-available picks up eligible cases and does not pick up ineligible ones"""
    caplog.set_level(logging.INFO)

    # GIVEN CASE ID of sample where read counts pass threshold
    case_id_success = "balsamic_case_wgs_paired_enough_reads"

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

    # THEN command exits with 1 because one of cases raised errors
    assert result.exit_code == 1

    # THEN it should successfully identify the one case eligible for auto-start
    assert case_id_success in caplog.text

    # THEN action of the case should be set to running
    assert balsamic_context["BalsamicAnalysisAPI"].store.family(case_id_success).action == "running"

    # THEN the ineligible case should NOT be ran
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
    """Test to ensure all parts of compound store-available command are executed given ideal conditions
    Test that sore-available picks up eligible cases and does not pick up ineligible ones"""
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
    # THEN command exits with 1 because one of the cases threw errors
    assert result.exit_code == 1
    assert case_id_success in caplog.text
    assert balsamic_context["BalsamicAnalysisAPI"].store.family(case_id_success).action == "running"

    balsamic_context["BalsamicAnalysisAPI"].housekeeper_api = real_housekeeper_api
    # WHEN running command
    result = cli_runner.invoke(store_available, ["--dry-run"], obj=balsamic_context)

    # THEN command exits successfully
    assert result.exit_code == 0

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
