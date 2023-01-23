import logging

from _pytest.logging import LogCaptureFixture
from click.testing import CliRunner
from pytest_mock import MockFixture

from cg.apps.hermes.hermes_api import HermesApi
from cg.apps.hermes.models import CGDeliverables
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.cli.workflow.rnafusion.base import (
    rnafusion,
    start,
    start_available,
    store,
    store_available,
    store_housekeeper,
)
from cg.constants import EXIT_SUCCESS
from cg.meta.workflow.rnafusion import RnafusionAnalysisAPI
from cg.models.cg_config import CGConfig


def test_rnafusion_no_args(cli_runner: CliRunner, rnafusion_context: CGConfig):
    """Test to see that running BALSAMIC without options prints help and doesn't result in an error."""
    # GIVEN no arguments or options besides the command call

    # WHEN running command
    result = cli_runner.invoke(rnafusion, [], obj=rnafusion_context)

    # THEN command runs successfully
    print(result.output)

    assert result.exit_code == EXIT_SUCCESS

    # THEN help should be printed
    assert "help" in result.output


def test_start(
    cli_runner: CliRunner,
    rnafusion_context: CGConfig,
    caplog: LogCaptureFixture,
    rnafusion_case_id: str,
    mock_config,
):
    """Test to ensure all parts of start command will run successfully given ideal conditions."""
    caplog.set_level(logging.INFO)

    # GIVEN case id
    case_id: str = rnafusion_case_id

    # GIVEN a mocked config

    # GIVEN decompression is not needed
    RnafusionAnalysisAPI.resolve_decompression.return_value = None

    # WHEN dry running with dry specified
    result = cli_runner.invoke(start, [case_id, "--dry-run"], obj=rnafusion_context)

    # THEN command should execute successfully
    assert result.exit_code == EXIT_SUCCESS
    assert case_id in caplog.text

    # THEN command should not include resume flag
    assert "-resume" not in caplog.text


def test_store_success(
    cli_runner: CliRunner,
    rnafusion_context: CGConfig,
    real_housekeeper_api: HousekeeperAPI,
    mock_deliverable,
    mock_analysis_finish,
    caplog: LogCaptureFixture,
    hermes_deliverables: dict,
    mocker,
    rnafusion_case_id: str,
):
    """Test to ensure all parts of store command are run successfully given ideal conditions."""
    caplog.set_level(logging.INFO)

    # GIVEN case-id for which we created a config file, deliverables file, and analysis_finish file
    case_id: str = rnafusion_case_id

    # Set Housekeeper to an empty real Housekeeper store
    rnafusion_context.housekeeper_api_: HousekeeperAPI = real_housekeeper_api
    rnafusion_context.meta_apis["analysis_api"].housekeeper_api = real_housekeeper_api

    # Make sure the bundle was not present in hk
    assert not rnafusion_context.housekeeper_api.bundle(case_id)

    # Make sure analysis not already stored in status_db
    assert not rnafusion_context.status_db.family(case_id).analyses

    # GIVEN that HermesAPI returns a deliverables output
    mocker.patch.object(HermesApi, "convert_deliverables")
    HermesApi.convert_deliverables.return_value = CGDeliverables(**hermes_deliverables)

    # WHEN running command
    result = cli_runner.invoke(store, [case_id], obj=rnafusion_context)
    # THEN bundle should be successfully added to HK and STATUSDB
    assert result.exit_code == EXIT_SUCCESS
    assert "Analysis successfully stored in Housekeeper" in caplog.text
    assert "Analysis successfully stored in StatusDB" in caplog.text
    assert rnafusion_context.status_db.family(case_id).analyses
    assert rnafusion_context.housekeeper_api.bundle(case_id)


def test_store_fail(
    cli_runner: CliRunner,
    rnafusion_context: CGConfig,
    real_housekeeper_api: HousekeeperAPI,
    mock_deliverable,
    mock_analysis_finish,
    caplog: LogCaptureFixture,
    hermes_deliverables: dict,
):
    """Test store command fails when a case did not finish."""
    caplog.set_level(logging.INFO)

    # GIVEN CASE ID where analysis finish is not mocked
    case_id_fail: str = "rnafusion_case_not_finished"

    # Set Housekeeper to an empty real Housekeeper store
    rnafusion_context.housekeeper_api_: HousekeeperAPI = real_housekeeper_api
    rnafusion_context.meta_apis["analysis_api"].housekeeper_api = real_housekeeper_api

    # Make sure the bundle was not present in hk
    assert not rnafusion_context.housekeeper_api.bundle(case_id_fail)

    # WHEN running command
    result_fail = cli_runner.invoke(store, [case_id_fail], obj=rnafusion_context)

    # THEN bundle exist status should be
    assert result_fail.exit_code != EXIT_SUCCESS


def test_start_available(
    cli_runner: CliRunner,
    rnafusion_context: CGConfig,
    caplog: LogCaptureFixture,
    mocker,
    rnafusion_case_id: str,
    mock_config,
):
    """Test to ensure all parts of compound start-available command are executed given ideal conditions
    Test that start-available picks up eligible cases and does not pick up ineligible ones."""
    caplog.set_level(logging.INFO)

    # GIVEN CASE ID of sample where read counts pass threshold
    case_id_success: str = rnafusion_case_id

    # GIVEN a mocked config

    # GIVEN decompression is not needed
    mocker.patch.object(RnafusionAnalysisAPI, "resolve_decompression")
    RnafusionAnalysisAPI.resolve_decompression.return_value = None

    # WHEN running command
    result = cli_runner.invoke(start_available, ["--dry-run"], obj=rnafusion_context)

    # THEN command exits with 0
    assert result.exit_code == EXIT_SUCCESS

    # THEN it should successfully identify the one case eligible for auto-start
    assert case_id_success in caplog.text


def test_store_available(
    tmpdir_factory,
    cli_runner: CliRunner,
    rnafusion_context: CGConfig,
    real_housekeeper_api,
    mock_deliverable,
    mock_analysis_finish,
    caplog: LogCaptureFixture,
    mocker,
    hermes_deliverables,
    rnafusion_case_id: str,
    mock_config,
):
    """Test to ensure all parts of compound store-available command are executed given ideal conditions
    Test that sore-available picks up eligible cases and does not pick up ineligible ones."""
    caplog.set_level(logging.INFO)

    # GIVEN CASE ID of sample where read counts pass threshold
    case_id_success: str = rnafusion_case_id

    # GIVEN that HermesAPI returns a deliverables output
    mocker.patch.object(HermesApi, "convert_deliverables")
    HermesApi.convert_deliverables.return_value = CGDeliverables(**hermes_deliverables)

    # GIVEN a mocked config

    # Ensure case was successfully picked up by start-available and status set to running
    result = cli_runner.invoke(start_available, ["--dry-run"], obj=rnafusion_context)
    rnafusion_context.status_db.family(case_id_success).action = "running"
    rnafusion_context.status_db.commit()

    # THEN command exits with 0
    assert result.exit_code == EXIT_SUCCESS
    assert case_id_success in caplog.text
    assert rnafusion_context.status_db.family(case_id_success).action == "running"

    rnafusion_context.housekeeper_api_ = real_housekeeper_api
    rnafusion_context.meta_apis["analysis_api"].housekeeper_api = real_housekeeper_api

    # WHEN running command
    result = cli_runner.invoke(store_available, obj=rnafusion_context)

    # THEN command exits successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN case id with analysis_finish gets picked up
    assert case_id_success in caplog.text

    # THEN case has analyses
    assert rnafusion_context.status_db.family(case_id_success).analyses

    # THEN bundle can be found in Housekeeper
    assert rnafusion_context.housekeeper_api.bundle(case_id_success)

    # THEN bundle added successfully and action set to None
    assert rnafusion_context.status_db.family(case_id_success).action is None
