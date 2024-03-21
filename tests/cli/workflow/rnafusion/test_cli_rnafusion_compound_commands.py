import logging

from _pytest.logging import LogCaptureFixture
from click.testing import CliRunner

from cg.apps.hermes.hermes_api import HermesApi
from cg.apps.hermes.models import CGDeliverables
from cg.cli.workflow.rnafusion.base import start_available, store_available
from cg.constants import EXIT_SUCCESS
from cg.meta.workflow.rnafusion import RnafusionAnalysisAPI
from cg.models.cg_config import CGConfig


def test_store_available(
    cli_runner: CliRunner,
    rnafusion_context: CGConfig,
    real_housekeeper_api,
    rnafusion_hermes_deliverables,
    rnafusion_case_id: str,
    deliverables_template_content: list[dict],
    rnafusion_mock_deliverable_dir,
    rnafusion_mock_analysis_finish,
    mock_config,
    mocker,
    caplog: LogCaptureFixture,
):
    """Test to ensure all parts of compound store-available command are executed given ideal conditions
    Test that store-available picks up eligible cases and does not pick up ineligible ones."""
    caplog.set_level(logging.INFO)

    # GIVEN CASE ID of sample where read counts pass threshold
    case_id_success: str = rnafusion_case_id

    # GIVEN a mocked deliverables template
    mocker.patch.object(
        RnafusionAnalysisAPI,
        "get_deliverables_template_content",
        return_value=deliverables_template_content,
    )

    # GIVEN that HermesAPI returns a deliverables output
    mocker.patch.object(HermesApi, "convert_deliverables")
    HermesApi.convert_deliverables.return_value = CGDeliverables(**rnafusion_hermes_deliverables)

    # GIVEN a mocked config

    # Ensure case was successfully picked up by start-available and status set to running
    result = cli_runner.invoke(start_available, ["--dry-run"], obj=rnafusion_context)
    rnafusion_context.status_db.get_case_by_internal_id(case_id_success).action = "running"
    rnafusion_context.status_db.session.commit()

    # THEN command exits with 0
    assert result.exit_code == EXIT_SUCCESS
    assert case_id_success in caplog.text
    assert rnafusion_context.status_db.get_case_by_internal_id(case_id_success).action == "running"

    rnafusion_context.housekeeper_api_ = real_housekeeper_api
    rnafusion_context.meta_apis["analysis_api"].housekeeper_api = real_housekeeper_api

    # WHEN running command
    result = cli_runner.invoke(store_available, obj=rnafusion_context)

    # THEN command exits successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN case id with analysis_finish gets picked up
    assert case_id_success in caplog.text

    # THEN case has analyses
    assert rnafusion_context.status_db.get_case_by_internal_id(case_id_success).analyses

    # THEN bundle can be found in Housekeeper
    assert rnafusion_context.housekeeper_api.bundle(case_id_success)

    # THEN bundle added successfully and action set to None
    assert rnafusion_context.status_db.get_case_by_internal_id(case_id_success).action is None
