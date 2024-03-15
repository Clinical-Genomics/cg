import logging

import pytest
from _pytest.fixtures import FixtureRequest
from _pytest.logging import LogCaptureFixture
from click.testing import CliRunner

from cg.apps.hermes.hermes_api import HermesApi
from cg.apps.hermes.models import CGDeliverables
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.cli.workflow.base import workflow as workflow_cli
from cg.constants import EXIT_SUCCESS, Workflow
from cg.meta.workflow.nf_analysis import NfAnalysisAPI
from cg.models.cg_config import CGConfig
from tests.cli.workflow.conftest import mock_analysis_flow_cell


@pytest.mark.parametrize(
    "workflow",
    [Workflow.RNAFUSION, Workflow.TAXPROFILER],
)
def test_store_success(
    cli_runner: CliRunner,
    real_housekeeper_api: HousekeeperAPI,
    workflow: Workflow,
    caplog: LogCaptureFixture,
    deliverables_template_content: list[dict],
    request: FixtureRequest,
    mocker,
):
    """Test to ensure all parts of store command are run successfully given ideal conditions."""
    caplog.set_level(logging.INFO)

    # GIVEN a case for which we mocked files created after a successful run

    # GIVEN each fixture is being initialised
    context: CGConfig = request.getfixturevalue(f"{workflow}_context")
    case_id: str = request.getfixturevalue(f"{workflow}_case_id")
    hermes_deliverables: dict = request.getfixturevalue(f"{workflow}_hermes_deliverables")
    request.getfixturevalue(f"{workflow}_mock_deliverable_dir")
    request.getfixturevalue(f"{workflow}_mock_analysis_finish")

    # GIVEN a mocked deliverables template
    mocker.patch.object(
        NfAnalysisAPI,
        "get_deliverables_template_content",
        return_value=deliverables_template_content,
    )

    # Set Housekeeper to an empty real Housekeeper store
    context.housekeeper_api_: HousekeeperAPI = real_housekeeper_api
    context.meta_apis["analysis_api"].housekeeper_api = real_housekeeper_api

    # Make sure the bundle was not present in hk
    assert not context.housekeeper_api.bundle(case_id)

    # Make sure analysis not already stored in status_db
    assert not context.status_db.get_case_by_internal_id(internal_id=case_id).analyses

    # GIVEN that HermesAPI returns a deliverables output
    mocker.patch.object(HermesApi, "convert_deliverables")
    HermesApi.convert_deliverables.return_value = CGDeliverables(**hermes_deliverables)

    # WHEN running command
    result = cli_runner.invoke(workflow_cli, [workflow, "store", case_id], obj=context)

    # THEN bundle should be successfully added to Housekeeper and StatusDB
    assert result.exit_code == EXIT_SUCCESS
    assert "Analysis successfully stored in Housekeeper" in caplog.text
    assert "Analysis successfully stored in StatusDB" in caplog.text
    assert context.status_db.get_case_by_internal_id(internal_id=case_id).analyses
    assert context.housekeeper_api.bundle(case_id)


@pytest.mark.parametrize(
    "workflow",
    [Workflow.RNAFUSION, Workflow.TAXPROFILER],
)
def test_store_fail(
    cli_runner: CliRunner,
    workflow: Workflow,
    rnafusion_context: CGConfig,
    real_housekeeper_api: HousekeeperAPI,
    deliverables_template_content: list[dict],
    caplog: LogCaptureFixture,
    request: FixtureRequest,
    mocker,
):
    """Test store command fails when a case did not finish for a workflow."""
    caplog.set_level(logging.INFO)

    # GIVEN each fixture is being initialised
    context: CGConfig = request.getfixturevalue(f"{workflow}_context")

    # GIVEN CASE ID where analysis finish is not mocked
    case_id_fail: str = request.getfixturevalue(f"{workflow}_case_id")

    # GIVEN a mocked deliverables template
    mocker.patch.object(
        NfAnalysisAPI,
        "get_deliverables_template_content",
        return_value=deliverables_template_content,
    )

    # Set Housekeeper to an empty real Housekeeper store
    context.housekeeper_api_: HousekeeperAPI = real_housekeeper_api
    context.meta_apis["analysis_api"].housekeeper_api = real_housekeeper_api

    # Make sure the bundle was not present in hk
    assert not context.housekeeper_api.bundle(case_id_fail)

    # WHEN running command
    result_fail = cli_runner.invoke(workflow_cli, [workflow, "store", case_id_fail], obj=context)

    # THEN bundle exist status should be
    assert result_fail.exit_code != EXIT_SUCCESS
