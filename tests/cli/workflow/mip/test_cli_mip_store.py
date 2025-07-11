from datetime import datetime
from pathlib import Path
from unittest.mock import ANY

import pytest
from click.testing import CliRunner
from pytest import LogCaptureFixture

from cg.apps.hermes.hermes_api import HermesApi
from cg.apps.housekeeper.models import InputBundle
from cg.cli.workflow.mip_dna.base import store, store_available
from cg.constants import EXIT_SUCCESS
from cg.meta.workflow.mip_dna import MipDNAAnalysisAPI
from cg.models.cg_config import CGConfig


def test_cli_store_dry_no_case(
    cli_runner: CliRunner,
    mip_case_id_non_existing: str,
    mip_dna_context: CGConfig,
    caplog,
):
    caplog.set_level("ERROR")

    # GIVEN a case_id that does not exist in database

    # WHEN running command in dry-run mode
    result = cli_runner.invoke(store, [mip_case_id_non_existing, "--dry-run"], obj=mip_dna_context)

    # THEN command does not terminate successfully
    assert result.exit_code != EXIT_SUCCESS

    # THEN logging informs about the case_id not existing
    assert mip_case_id_non_existing in caplog.text
    assert "could not be found" in caplog.text


def test_cli_store(
    cli_runner: CliRunner,
    mip_case_id: str,
    mip_deliverables_file: Path,
    mip_hermes_dna_deliverables_response_data: InputBundle,
    mip_dna_context: CGConfig,
    timestamp_yesterday: datetime,
    case_qc_sample_info_path: Path,
    caplog: LogCaptureFixture,
    mocker,
):
    caplog.set_level("INFO")
    mip_analysis_api: MipDNAAnalysisAPI = mip_dna_context.meta_apis["analysis_api"]

    # GIVEN a case_id that does exist in database

    # GIVEN that case action is "running"
    mip_analysis_api.set_statusdb_action(case_id=mip_case_id, action="running")

    # GIVEN deliverables were generated and could be found
    mocker.patch.object(MipDNAAnalysisAPI, "get_deliverables_file_path")
    MipDNAAnalysisAPI.get_deliverables_file_path.return_value = mip_deliverables_file

    # GIVEN the same timestamp is attained when storing analysis in different databases
    mocker.patch.object(MipDNAAnalysisAPI, "get_date_from_file_path")
    MipDNAAnalysisAPI.get_date_from_file_path.return_value = timestamp_yesterday

    # mock the update_analysis_as_completed_statusdb method so we can assert it was called
    mocker.patch.object(MipDNAAnalysisAPI, "update_analysis_as_completed_statusdb")

    # GIVEN Hermes parses deliverables and generates a valid response
    mocker.patch.object(HermesApi, "create_housekeeper_bundle")
    HermesApi.create_housekeeper_bundle.return_value = mip_hermes_dna_deliverables_response_data

    # GIVEN sample_info were generated and could be found
    mocker.patch.object(MipDNAAnalysisAPI, "get_sample_info_path")
    MipDNAAnalysisAPI.get_sample_info_path.return_value = case_qc_sample_info_path

    # WHEN running command
    result = cli_runner.invoke(store, [mip_case_id], obj=mip_dna_context)

    # THEN command terminates successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN log informs that analysis was stored in Housekeeper and StatusDB
    assert "stored in Housekeeper" in caplog.text

    # THEN the analysis was updated in statusdb
    MipDNAAnalysisAPI.update_analysis_as_completed_statusdb.assert_called_with(
        case_id=mip_case_id, hk_version_id=ANY, comment=ANY, dry_run=False, force=False
    )


def test_cli_store_bundle_already_added(
    cli_runner: CliRunner,
    mip_case_id: str,
    mip_deliverables_file,
    mip_hermes_dna_deliverables_response_data,
    mip_dna_context: CGConfig,
    timestamp_yesterday,
    caplog,
    mocker,
):
    caplog.set_level("INFO")
    mip_analysis_api: MipDNAAnalysisAPI = mip_dna_context.meta_apis["analysis_api"]

    # GIVEN a case_id that does exist in database

    # GIVEN that case action is "running"
    mip_analysis_api.set_statusdb_action(case_id=mip_case_id, action="running")

    # GIVEN deliverables were generated and could be found
    mocker.patch.object(MipDNAAnalysisAPI, "get_deliverables_file_path")
    MipDNAAnalysisAPI.get_deliverables_file_path.return_value = mip_deliverables_file

    # GIVEN the same timestamp is attained when storing analysis in different databases
    mocker.patch.object(MipDNAAnalysisAPI, "get_date_from_file_path")
    MipDNAAnalysisAPI.get_date_from_file_path.return_value = timestamp_yesterday

    # GIVEN Hermes parses deliverables and generates a valid response
    mocker.patch.object(HermesApi, "create_housekeeper_bundle")
    HermesApi.create_housekeeper_bundle.return_value = mip_hermes_dna_deliverables_response_data

    # GIVEN deliverables have already been stored in Housekeeper
    cli_runner.invoke(store, [mip_case_id], obj=mip_dna_context)

    # WHEN running command
    result = cli_runner.invoke(store, [mip_case_id], obj=mip_dna_context)

    # THEN command does not terminate successfully
    assert result.exit_code != EXIT_SUCCESS

    # THEN log informs that storing deliverables failed
    assert "Error storing deliverables" in caplog.text


@pytest.mark.usefixtures("mip_case_dirs")
def test_cli_store_available_case_is_running(
    cli_runner: CliRunner,
    mip_case_id: str,
    mip_deliverables_file: Path,
    mip_hermes_dna_deliverables_response_data: InputBundle,
    mip_dna_context: CGConfig,
    timestamp_yesterday: datetime,
    case_qc_sample_info_path: Path,
    caplog: LogCaptureFixture,
    mocker,
):
    caplog.set_level("INFO")
    mip_analysis_api: MipDNAAnalysisAPI = mip_dna_context.meta_apis["analysis_api"]
    # GIVEN a case_id that does exist in database

    # GIVEN that case action is "running"
    mip_analysis_api.set_statusdb_action(case_id=mip_case_id, action="running")

    # GIVEN deliverables were generated and could be found
    mocker.patch.object(MipDNAAnalysisAPI, "get_deliverables_file_path")
    MipDNAAnalysisAPI.get_deliverables_file_path.return_value = mip_deliverables_file

    # GIVEN the same timestamp is attained when storing analysis in different databases
    mocker.patch.object(MipDNAAnalysisAPI, "get_date_from_file_path")
    MipDNAAnalysisAPI.get_date_from_file_path.return_value = timestamp_yesterday

    # mock the update_analysis_as_completed_statusdb method so we can assert it was called
    mocker.patch.object(MipDNAAnalysisAPI, "update_analysis_as_completed_statusdb")

    # GIVEN Hermes parses deliverables and generates a valid response
    mocker.patch.object(HermesApi, "create_housekeeper_bundle")
    HermesApi.create_housekeeper_bundle.return_value = mip_hermes_dna_deliverables_response_data

    # GIVEN sample_info were generated and could be found
    mocker.patch.object(MipDNAAnalysisAPI, "get_sample_info_path")
    MipDNAAnalysisAPI.get_sample_info_path.return_value = case_qc_sample_info_path

    # GIVEN that the case analysis is finished in trailblazer
    mocker.patch.object(MipDNAAnalysisAPI, "get_cases_to_store")
    MipDNAAnalysisAPI.get_cases_to_store.return_value = [
        mip_analysis_api.status_db.get_case_by_internal_id(internal_id=mip_case_id)
    ]

    # WHEN running command
    result = cli_runner.invoke(store_available, [], obj=mip_dna_context)

    # THEN command terminates successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN analysis data is stored in Housekeeper and StatusDB
    assert "stored in Housekeeper" in caplog.text

    # THEN log informs about eligible case
    assert mip_case_id in caplog.text

    # THEN the analysis was updated in statusdb
    MipDNAAnalysisAPI.update_analysis_as_completed_statusdb.assert_called_with(
        case_id=mip_case_id, hk_version_id=ANY, comment=ANY, dry_run=False, force=False
    )


def test_cli_store_available_case_not_running(
    cli_runner: CliRunner,
    mip_case_id: str,
    mip_deliverables_file,
    mip_hermes_dna_deliverables_response_data,
    mip_dna_context: CGConfig,
    timestamp_yesterday,
    caplog,
    mocker,
):
    caplog.set_level("INFO")
    mip_analysis_api: MipDNAAnalysisAPI = mip_dna_context.meta_apis["analysis_api"]

    # GIVEN a case_id that does exist in database

    # GIVEN that case action is None
    mip_analysis_api.status_db.get_case_by_internal_id(internal_id=mip_case_id).action = None
    mip_analysis_api.status_db.session.commit()

    # GIVEN deliverables were generated and could be found
    mocker.patch.object(MipDNAAnalysisAPI, "get_deliverables_file_path")
    MipDNAAnalysisAPI.get_deliverables_file_path.return_value = mip_deliverables_file

    # GIVEN the same timestamp is attained when storing analysis in different databases
    mocker.patch.object(MipDNAAnalysisAPI, "get_date_from_file_path")
    MipDNAAnalysisAPI.get_date_from_file_path.return_value = timestamp_yesterday

    # GIVEN Hermes parses deliverables and generates a valid response
    mocker.patch.object(HermesApi, "create_housekeeper_bundle")
    HermesApi.create_housekeeper_bundle.return_value = mip_hermes_dna_deliverables_response_data

    # WHEN running command
    result = cli_runner.invoke(store_available, [], obj=mip_dna_context)

    # THEN command terminates successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN case is not picked up by query and is not in the log
    assert mip_case_id not in caplog.text

    # THEN nothing is stored in Housekeeper
    assert "stored in Housekeeper" not in caplog.text
