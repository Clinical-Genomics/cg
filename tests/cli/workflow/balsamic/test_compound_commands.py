import logging
from pathlib import Path
from unittest.mock import ANY, create_autospec

import pytest
from click.testing import CliRunner

from cg.apps.hermes.hermes_api import HermesApi
from cg.apps.hermes.models import CGDeliverables
from cg.cli.workflow.balsamic.base import balsamic, store, store_available
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
        case_id=case_id, hk_version_id=ANY, comment=ANY, dry_run=False, force=False
    )


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
    mock_update_analysis = mocker.patch.object(AnalysisAPI, "update_analysis_as_completed_statusdb")

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

    # GIVEN a mocked Housekeeper API
    balsamic_context.housekeeper_api_ = real_housekeeper_api
    balsamic_context.meta_apis["analysis_api"].housekeeper_api = real_housekeeper_api

    # GIVEN a mocked report deliver command
    mocker.patch.object(BalsamicAnalysisAPI, "report_deliver", return_value=None)

    # WHEN running command
    mocker.patch.object(
        BalsamicAnalysisAPI,
        "get_cases_to_store",
        return_value=[create_autospec(Case, internal_id=case_id_success)],
    )
    result = cli_runner.invoke(store_available, obj=balsamic_context)

    # THEN command exits successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN case id with analysis_finish gets picked up
    assert case_id_success in caplog.text

    # THEN the analysis of the successful case was updated in status DB
    mock_update_analysis.assert_called_once_with(
        case_id=case_id_success, hk_version_id=ANY, comment=ANY, dry_run=False, force=False
    )

    # THEN bundle can be found in Housekeeper
    assert balsamic_context.housekeeper_api.bundle(case_id_success)

    # THEN bundle added successfully and action set to None
    assert balsamic_context.status_db.get_case_by_internal_id(case_id_success).action is None
