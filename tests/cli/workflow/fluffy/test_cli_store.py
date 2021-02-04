from cg.apps.hermes.hermes_api import HermesApi
from cg.cli.workflow.fluffy.base import store, store_available
from cg.constants import EXIT_SUCCESS, EXIT_FAIL
from cg.meta.workflow.fluffy import FluffyAnalysisAPI
import datetime as dt


def test_cli_store(
    cli_runner,
    fluffy_case_id_existing,
    deliverables_yaml_fixture_path,
    fluffy_hermes_deliverables_response_data,
    fluffy_context,
    timestamp_yesterday,
    caplog,
    mocker,
):
    caplog.set_level("INFO")

    fluffy_analysis_api: FluffyAnalysisAPI = fluffy_context["fluffy_analysis_api"]
    fluffy_analysis_api.set_statusdb_action(case_id=fluffy_case_id_existing, action="running")

    mocker.patch.object(FluffyAnalysisAPI, "get_deliverables_path")
    FluffyAnalysisAPI.get_deliverables_path.return_value = deliverables_yaml_fixture_path

    mocker.patch.object(FluffyAnalysisAPI, "get_date_from_file_path")
    FluffyAnalysisAPI.get_date_from_file_path.return_value = timestamp_yesterday

    mocker.patch.object(HermesApi, "create_housekeeper_bundle")
    HermesApi.create_housekeeper_bundle.return_value = fluffy_hermes_deliverables_response_data

    result = cli_runner.invoke(store, [fluffy_case_id_existing], obj=fluffy_context)

    assert result.exit_code == EXIT_SUCCESS
    assert "stored in Housekeeper" in caplog.text
    assert "stored in StatusDB" in caplog.text
    assert not fluffy_analysis_api.status_db.family(fluffy_case_id_existing).action


def test_cli_store_bundle_already_added(
    cli_runner,
    fluffy_case_id_existing,
    deliverables_yaml_fixture_path,
    fluffy_hermes_deliverables_response_data,
    fluffy_context,
    timestamp_yesterday,
    caplog,
    mocker,
):
    caplog.set_level("ERROR")

    mocker.patch.object(FluffyAnalysisAPI, "get_deliverables_path")
    FluffyAnalysisAPI.get_deliverables_path.return_value = deliverables_yaml_fixture_path

    mocker.patch.object(FluffyAnalysisAPI, "get_date_from_file_path")
    FluffyAnalysisAPI.get_date_from_file_path.return_value = timestamp_yesterday

    mocker.patch.object(HermesApi, "create_housekeeper_bundle")
    HermesApi.create_housekeeper_bundle.return_value = fluffy_hermes_deliverables_response_data

    cli_runner.invoke(store, [fluffy_case_id_existing], obj=fluffy_context)
    result = cli_runner.invoke(store, [fluffy_case_id_existing], obj=fluffy_context)

    assert result.exit_code != EXIT_SUCCESS
    assert "Error storing deliverables" in caplog.text


def test_cli_store_available_case_is_running(
    cli_runner,
    fluffy_case_id_existing,
    deliverables_yaml_fixture_path,
    fluffy_hermes_deliverables_response_data,
    fluffy_context,
    timestamp_yesterday,
    caplog,
    mocker,
):
    caplog.set_level("INFO")

    fluffy_analysis_api: FluffyAnalysisAPI = fluffy_context["fluffy_analysis_api"]
    fluffy_analysis_api.set_statusdb_action(case_id=fluffy_case_id_existing, action="running")

    mocker.patch.object(FluffyAnalysisAPI, "get_deliverables_path")
    FluffyAnalysisAPI.get_deliverables_path.return_value = deliverables_yaml_fixture_path

    mocker.patch.object(FluffyAnalysisAPI, "get_date_from_file_path")
    FluffyAnalysisAPI.get_date_from_file_path.return_value = timestamp_yesterday

    mocker.patch.object(HermesApi, "create_housekeeper_bundle")
    HermesApi.create_housekeeper_bundle.return_value = fluffy_hermes_deliverables_response_data

    result = cli_runner.invoke(store_available, [], obj=fluffy_context)

    assert result.exit_code == EXIT_SUCCESS
    assert "stored in Housekeeper" in caplog.text
    assert "stored in StatusDB" in caplog.text
    assert fluffy_case_id_existing in caplog.text
    assert not fluffy_analysis_api.status_db.family(fluffy_case_id_existing).action


def test_cli_store_available_case_not_running(
    cli_runner,
    fluffy_case_id_existing,
    deliverables_yaml_fixture_path,
    fluffy_hermes_deliverables_response_data,
    fluffy_context,
    timestamp_yesterday,
    caplog,
    mocker,
):

    fluffy_analysis_api: FluffyAnalysisAPI = fluffy_context["fluffy_analysis_api"]
    fluffy_analysis_api.status_db.family(fluffy_case_id_existing).action = None
    fluffy_analysis_api.status_db.commit()

    caplog.set_level("INFO")

    mocker.patch.object(FluffyAnalysisAPI, "get_deliverables_path")
    FluffyAnalysisAPI.get_deliverables_path.return_value = deliverables_yaml_fixture_path

    mocker.patch.object(FluffyAnalysisAPI, "get_date_from_file_path")
    FluffyAnalysisAPI.get_date_from_file_path.return_value = timestamp_yesterday

    mocker.patch.object(HermesApi, "create_housekeeper_bundle")
    HermesApi.create_housekeeper_bundle.return_value = fluffy_hermes_deliverables_response_data

    result = cli_runner.invoke(store_available, [], obj=fluffy_context)

    assert result.exit_code == EXIT_SUCCESS
    assert fluffy_case_id_existing not in caplog.text
