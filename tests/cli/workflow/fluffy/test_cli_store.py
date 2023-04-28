from cg.apps.hermes.hermes_api import HermesApi
from cg.cli.workflow.fluffy.base import store, store_available
from cg.constants import EXIT_SUCCESS
from cg.meta.workflow.fluffy import FluffyAnalysisAPI
from cg.models.cg_config import CGConfig
from click.testing import CliRunner


def test_cli_store_dry_no_case(
    cli_runner: CliRunner,
    fluffy_case_id_non_existing: str,
    fluffy_context: CGConfig,
    caplog,
):
    caplog.set_level("ERROR")

    # GIVEN a case_id that does not exist in database

    # WHEN running command in dry-run mode
    result = cli_runner.invoke(
        store, [fluffy_case_id_non_existing, "--dry-run"], obj=fluffy_context
    )

    # THEN command does not terminate successfully
    assert result.exit_code != EXIT_SUCCESS

    # THEN logging informs about the case_id not existing
    assert fluffy_case_id_non_existing in caplog.text
    assert "could not be found" in caplog.text


def test_cli_store(
    cli_runner: CliRunner,
    fluffy_case_id_existing: str,
    deliverables_yaml_fixture_path,
    fluffy_hermes_deliverables_response_data,
    fluffy_context: CGConfig,
    timestamp_yesterday,
    caplog,
    mocker,
):
    caplog.set_level("INFO")
    fluffy_analysis_api: FluffyAnalysisAPI = fluffy_context.meta_apis["analysis_api"]

    # GIVEN a case_id that does exist in database

    # GIVEN that case action is "running"
    fluffy_analysis_api.set_statusdb_action(case_id=fluffy_case_id_existing, action="running")

    # GIVEN deliverables were generated and could be found
    mocker.patch.object(FluffyAnalysisAPI, "get_deliverables_file_path")
    FluffyAnalysisAPI.get_deliverables_file_path.return_value = deliverables_yaml_fixture_path

    # GIVEN the same timestamp is attained when storing analysis in different databases
    mocker.patch.object(FluffyAnalysisAPI, "get_date_from_file_path")
    FluffyAnalysisAPI.get_date_from_file_path.return_value = timestamp_yesterday

    # GIVEN Hermes parses deliverables and generates a valid response
    mocker.patch.object(HermesApi, "create_housekeeper_bundle")
    HermesApi.create_housekeeper_bundle.return_value = fluffy_hermes_deliverables_response_data

    # WHEN running command
    result = cli_runner.invoke(store, [fluffy_case_id_existing], obj=fluffy_context)

    # THEN command terminates successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN log informs that analysis was stored in Housekeeper and StatusDB
    assert "stored in Housekeeper" in caplog.text
    assert "stored in StatusDB" in caplog.text

    # THEN action of case in StatusDB is set to None
    assert not fluffy_analysis_api.status_db.get_case_by_internal_id(
        internal_id=fluffy_case_id_existing
    ).action


def test_cli_store_bundle_already_added(
    cli_runner: CliRunner,
    fluffy_case_id_existing,
    deliverables_yaml_fixture_path,
    fluffy_hermes_deliverables_response_data,
    fluffy_context: CGConfig,
    timestamp_yesterday,
    caplog,
    mocker,
):
    caplog.set_level("ERROR")
    # GIVEN a case_id that does exist in database

    # GIVEN deliverables were generated and could be found
    mocker.patch.object(FluffyAnalysisAPI, "get_deliverables_file_path")
    FluffyAnalysisAPI.get_deliverables_file_path.return_value = deliverables_yaml_fixture_path

    # GIVEN the same timestamp is attained when storing analysis in different databases
    mocker.patch.object(FluffyAnalysisAPI, "get_date_from_file_path")
    FluffyAnalysisAPI.get_date_from_file_path.return_value = timestamp_yesterday

    # GIVEN Hermes parses deliverables and generates a valid response
    mocker.patch.object(HermesApi, "create_housekeeper_bundle")
    HermesApi.create_housekeeper_bundle.return_value = fluffy_hermes_deliverables_response_data

    # GIVEN deliverables have already been stored in Housekeeper
    cli_runner.invoke(store, [fluffy_case_id_existing], obj=fluffy_context)

    # WHEN running command
    result = cli_runner.invoke(store, [fluffy_case_id_existing], obj=fluffy_context)

    # THEN command does not terminate successfully
    assert result.exit_code != EXIT_SUCCESS

    # THEN log informs that storing deliverables failed
    assert "Error storing deliverables" in caplog.text


def test_cli_store_available_case_is_running(
    cli_runner: CliRunner,
    fluffy_case_id_existing,
    deliverables_yaml_fixture_path,
    fluffy_hermes_deliverables_response_data,
    fluffy_context: CGConfig,
    timestamp_yesterday,
    caplog,
    mocker,
):
    caplog.set_level("INFO")
    fluffy_analysis_api: FluffyAnalysisAPI = fluffy_context.meta_apis["analysis_api"]

    # GIVEN a case_id that does exist in database

    # GIVEN that case action is "running"
    fluffy_analysis_api.set_statusdb_action(case_id=fluffy_case_id_existing, action="running")

    # GIVEN deliverables were generated and could be found
    mocker.patch.object(FluffyAnalysisAPI, "get_analysis_finish_path")
    FluffyAnalysisAPI.get_analysis_finish_path.return_value = deliverables_yaml_fixture_path

    # GIVEN the same timestamp is attained when storing analysis in different databases
    mocker.patch.object(FluffyAnalysisAPI, "get_date_from_file_path")
    FluffyAnalysisAPI.get_date_from_file_path.return_value = timestamp_yesterday

    # GIVEN Hermes parses deliverables and generates a valid response
    mocker.patch.object(HermesApi, "create_housekeeper_bundle")
    HermesApi.create_housekeeper_bundle.return_value = fluffy_hermes_deliverables_response_data

    # WHEN running command
    result = cli_runner.invoke(store_available, [], obj=fluffy_context)

    # THEN command terminates successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN analysis data is stored in Housekeeper and StatusDB
    assert "stored in Housekeeper" in caplog.text
    assert "stored in StatusDB" in caplog.text

    # THEN log informs about eligible case
    assert fluffy_case_id_existing in caplog.text

    # THEN case action is set to None after storing
    assert not fluffy_analysis_api.status_db.get_case_by_internal_id(
        internal_id=fluffy_case_id_existing
    ).action


def test_cli_store_available_case_not_running(
    cli_runner: CliRunner,
    fluffy_case_id_existing,
    deliverables_yaml_fixture_path,
    fluffy_hermes_deliverables_response_data,
    fluffy_context: CGConfig,
    timestamp_yesterday,
    caplog,
    mocker,
):
    caplog.set_level("INFO")
    fluffy_analysis_api: FluffyAnalysisAPI = fluffy_context.meta_apis["analysis_api"]

    # GIVEN a case_id that does exist in database

    # GIVEN that case action is None
    fluffy_analysis_api.status_db.get_case_by_internal_id(
        internal_id=fluffy_case_id_existing
    ).action = None
    fluffy_analysis_api.status_db.session.commit()

    # GIVEN deliverables were generated and could be found
    mocker.patch.object(FluffyAnalysisAPI, "get_deliverables_file_path")
    FluffyAnalysisAPI.get_deliverables_file_path.return_value = deliverables_yaml_fixture_path

    # GIVEN the same timestamp is attained when storing analysis in different databases
    mocker.patch.object(FluffyAnalysisAPI, "get_date_from_file_path")
    FluffyAnalysisAPI.get_date_from_file_path.return_value = timestamp_yesterday

    # GIVEN Hermes parses deliverables and generates a valid response
    mocker.patch.object(HermesApi, "create_housekeeper_bundle")
    HermesApi.create_housekeeper_bundle.return_value = fluffy_hermes_deliverables_response_data

    # WHEN running command
    result = cli_runner.invoke(store_available, [], obj=fluffy_context)

    # THEN command terminates successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN case is not picked up by query and is not in the log
    assert fluffy_case_id_existing not in caplog.text

    # THEN nothing is stored in Housekeeper
    assert "stored in Housekeeper" not in caplog.text
