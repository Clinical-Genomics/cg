import logging
from pathlib import Path
from unittest.mock import ANY

import pytest
from click.testing import CliRunner

from cg.apps.hermes.hermes_api import HermesApi
from cg.apps.hermes.models import CGDeliverables
from cg.cli.workflow.balsamic.base import balsamic, start, start_available, store, store_available
from cg.constants.constants import SequencingQCStatus
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.store.models import Case

EXIT_SUCCESS = 0


def test_balsamic_no_args(cli_runner: CliRunner, balsamic_context: CGConfig):
    """Test to see that running BALSAMIC without options prints help and doesn't result in an error"""
    # GIVEN no arguments or options besides the command call

    # WHEN running command
    result = cli_runner.invoke(balsamic, [], obj=balsamic_context)

    # THEN command runs successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN help should be printed
    assert "help" in result.output


def test_start(
    cli_runner: CliRunner,
    balsamic_context: CGConfig,
    mock_config,
    caplog,
    helpers,
    mock_analysis_illumina_run,
    mocker,
):
    """Test to ensure all parts of start command will run successfully given ideal conditions"""
    caplog.set_level(logging.INFO)

    # GIVEN case id for which we created a config file
    case_id = "balsamic_case_wgs_single"

    # WHEN dry running and config case already exists
    mocker.patch.object(BalsamicAnalysisAPI, "config_case", return_value=None)
    result = cli_runner.invoke(start, [case_id, "--dry-run"], obj=balsamic_context)

    # THEN command should execute successfully
    assert result.exit_code == EXIT_SUCCESS
    assert case_id in caplog.text


@pytest.mark.usefixtures("mock_config", "mock_deliverable")
def test_store(
    cli_runner: CliRunner,
    balsamic_context: CGConfig,
    real_housekeeper_api,
    caplog,
    hermes_deliverables,
    mocker,
):
    """Test to ensure all parts of store command are run successfully given ideal conditions"""
    caplog.set_level(logging.INFO)

    # GIVEN case-id for which we created a config file, deliverables file, and analysis_finish file
    case_id = "balsamic_case_wgs_single"

    # Set up a mock in the AnalysisAPI so that we can confirm it was called
    mocker.patch.object(AnalysisAPI, "update_analysis_as_completed_statusdb")

    # Set Housekeeper to an empty real Housekeeper store
    balsamic_context.housekeeper_api_ = real_housekeeper_api
    balsamic_context.meta_apis["analysis_api"].housekeeper_api = real_housekeeper_api

    # Make sure the bundle was not present in the store
    assert not balsamic_context.housekeeper_api.bundle(case_id)

    # Make sure analysis not already stored in StatusDB
    assert not balsamic_context.status_db.get_case_by_internal_id(internal_id=case_id).analyses

    # GIVEN a HermesAPI returning a deliverables output
    mocker.patch.object(HermesApi, "convert_deliverables")
    HermesApi.convert_deliverables.return_value = CGDeliverables(**hermes_deliverables)

    # WHEN running command
    result = cli_runner.invoke(store, [case_id, "--dry-run"], obj=balsamic_context)

    # THEN bundle should be successfully added to HK and STATUS
    assert result.exit_code == EXIT_SUCCESS
    assert "Analysis successfully stored in Housekeeper" in caplog.text
    assert balsamic_context.housekeeper_api.bundle(case_id)

    # THEN the analysis was updated in status DB
    AnalysisAPI.update_analysis_as_completed_statusdb.assert_called_with(
        case_id=case_id, comment=ANY, dry_run=False, force=False
    )


def test_start_available(
    cli_runner: CliRunner, balsamic_context: CGConfig, caplog, mocker, mock_analysis_illumina_run
):
    """Test to ensure all parts of compound start-available command are executed given ideal conditions
    Test that start-available picks up eligible cases and does not pick up ineligible ones"""
    caplog.set_level(logging.INFO)

    # GIVEN CASE ID of sample where read counts pass threshold
    case_id_success = "balsamic_case_wgs_single"

    # GIVEN CASE ID where read counts did not pass the threshold
    case_id_not_enough_reads = "balsamic_case_tgs_paired"

    # Ensure the config is mocked to run compound command
    Path.mkdir(
        Path(
            balsamic_context.meta_apis["analysis_api"].get_case_config_path(case_id_success)
        ).parent,
        exist_ok=True,
    )
    Path(balsamic_context.meta_apis["analysis_api"].get_case_config_path(case_id_success)).touch(
        exist_ok=True
    )

    # GIVEN decompression is not needed and config case performed
    mocker.patch.object(BalsamicAnalysisAPI, "resolve_decompression", return_value=None)
    mocker.patch.object(BalsamicAnalysisAPI, "config_case", return_value=None)

    # WHEN running command
    result = cli_runner.invoke(start_available, ["--dry-run"], obj=balsamic_context)

    # THEN command exits with a successful exit code
    assert result.exit_code == EXIT_SUCCESS

    # THEN it should successfully identify the one case eligible for auto-start
    assert f"Starting analysis for {case_id_success}" in caplog.text

    # THEN the ineligible case should NOT be run
    assert f"Starting analysis for {case_id_not_enough_reads}" not in caplog.text


def test_start_available_with_limit(
    cli_runner: CliRunner,
    balsamic_context: CGConfig,
    caplog,
    mocker,
    balsamic_analysis_api: BalsamicAnalysisAPI,
    mock_analysis_illumina_run,
):
    """Test that the balsamic start-available command picks up only the given max number of cases."""
    # GIVEN that the log messages are captured
    caplog.set_level(logging.INFO)

    # GIVEN a balsamic_context with 1 case that is ready for analysis

    # GIVEN that 1 additional case is also ready for analysis
    case: Case = balsamic_context.status_db.get_case_by_internal_id(
        internal_id="balsamic_case_tgs_single"
    )
    case.aggregated_sequencing_qc = SequencingQCStatus.PASSED

    # GIVEN that there are now 2 cases that are ready for analysis
    assert len(balsamic_analysis_api.get_cases_to_analyze()) == 2

    # GIVEN that decompression is not needed
    mocker.patch.object(BalsamicAnalysisAPI, "resolve_decompression", return_value=None)

    # WHEN running the command with limit=1
    result = cli_runner.invoke(start_available, ["--dry-run", "--limit", 1], obj=balsamic_context)

    # THEN command exits with a successful exit code
    assert result.exit_code == EXIT_SUCCESS

    # THEN only 1 case is picked up to start
    assert caplog.text.count("Starting analysis for") == 1


@pytest.mark.usefixtures("mock_config", "mock_deliverable", "mock_analysis_illumina_run")
def test_store_available(
    cli_runner: CliRunner,
    balsamic_context: CGConfig,
    real_housekeeper_api,
    caplog,
    mocker,
    hermes_deliverables,
):
    """Test to ensure all parts of compound store-available command are executed given ideal conditions
    Test that sore-available picks up eligible cases and does not pick up ineligible ones"""
    caplog.set_level(logging.INFO)

    # GIVEN CASE ID of sample where read counts pass threshold
    case_id_success = "balsamic_case_wgs_single"

    # GIVEN CASE ID where analysis finish is not mocked
    case_id_fail = "balsamic_case_wgs_paired"

    # Set up a mock in the AnalysisAPI so that we can confirm it was called
    mocker.patch.object(AnalysisAPI, "update_analysis_as_completed_statusdb")

    # Ensure the config is mocked for fail case to run compound command
    Path.mkdir(
        Path(balsamic_context.meta_apis["analysis_api"].get_case_config_path(case_id_fail)).parent,
        exist_ok=True,
    )
    Path(balsamic_context.meta_apis["analysis_api"].get_case_config_path(case_id_fail)).touch(
        exist_ok=True
    )

    # GIVEN that HermesAPI returns a deliverables output and config case performed
    hermes_deliverables["bundle_id"] = case_id_success
    mocker.patch.object(
        HermesApi, "convert_deliverables", return_value=CGDeliverables(**hermes_deliverables)
    )
    mocker.patch.object(BalsamicAnalysisAPI, "config_case", return_value=None)

    # Ensure case was successfully picked up by start-available and status set to running
    result = cli_runner.invoke(start_available, ["--dry-run"], obj=balsamic_context)
    balsamic_context.status_db.get_case_by_internal_id(case_id_success).action = "running"
    balsamic_context.status_db.session.commit()

    # THEN command exit with success
    assert result.exit_code == EXIT_SUCCESS
    assert case_id_success in caplog.text
    assert balsamic_context.status_db.get_case_by_internal_id(case_id_success).action == "running"

    # GIVEN a mocked Housekeeper API
    balsamic_context.housekeeper_api_ = real_housekeeper_api
    balsamic_context.meta_apis["analysis_api"].housekeeper_api = real_housekeeper_api

    # GIVEN a mocked report deliver command
    mocker.patch.object(BalsamicAnalysisAPI, "report_deliver", return_value=None)

    # WHEN running command
    result = cli_runner.invoke(store_available, obj=balsamic_context)

    # THEN command exits successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN case id with analysis_finish gets picked up
    assert case_id_success in caplog.text

    # THEN the analysis of the successful case was updated in status DB
    AnalysisAPI.update_analysis_as_completed_statusdb.assert_called_once_with(
        case_id=case_id_success, comment=ANY, dry_run=False, force=False
    )

    # THEN bundle can be found in Housekeeper
    assert balsamic_context.housekeeper_api.bundle(case_id_success)

    # THEN bundle added successfully and action set to None
    assert balsamic_context.status_db.get_case_by_internal_id(case_id_success).action is None
