import logging
from unittest.mock import ANY

import pytest
from _pytest.fixtures import FixtureRequest
from _pytest.logging import LogCaptureFixture
from click.testing import CliRunner

from cg.apps.hermes.hermes_api import HermesApi
from cg.apps.hermes.models import CGDeliverables
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.cli.workflow.base import workflow as workflow_cli
from cg.constants import EXIT_FAIL, EXIT_SUCCESS, Workflow
from cg.constants.constants import CaseActions
from cg.constants.nextflow import NEXTFLOW_WORKFLOWS
from cg.meta.workflow.nf_analysis import NfAnalysisAPI
from cg.models.cg_config import CGConfig


@pytest.mark.parametrize(
    "workflow",
    NEXTFLOW_WORKFLOWS + [Workflow.NALLO],
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
    context: CGConfig = request.getfixturevalue(f"{workflow}_context")

    # GIVEN a case for which we mocked files created after a successful run
    case_id: str = request.getfixturevalue(f"{workflow}_case_id")
    hermes_deliverables: dict = request.getfixturevalue(f"{workflow}_hermes_deliverables")
    request.getfixturevalue(f"{workflow}_mock_deliverable_dir")
    request.getfixturevalue(f"{workflow}_mock_analysis_finish")
    deliverables_response_data = request.getfixturevalue(f"{workflow}_deliverables_response_data")

    # GIVEN a mocked deliverables template
    mocker.patch.object(
        NfAnalysisAPI,
        "get_deliverables_template_content",
        return_value=deliverables_template_content,
    )

    # GIVEN that the Housekeeper store is empty
    context.housekeeper_api_ = real_housekeeper_api
    context.meta_apis["analysis_api"].housekeeper_api = real_housekeeper_api

    # GIVEN that the bundle is not present in Housekeeper
    assert not context.housekeeper_api.bundle(case_id)

    # GIVEN that the analysis is not already stored in status_db
    assert not context.status_db.get_case_by_internal_id(internal_id=case_id).analyses

    # mock update_analysis_as_completed_statusdb so we can assert is was called
    mocker.patch.object(NfAnalysisAPI, "update_analysis_as_completed_statusdb")

    # GIVEN that HermesAPI returns a deliverables output
    mocker.patch.object(HermesApi, "convert_deliverables")
    HermesApi.convert_deliverables.return_value = CGDeliverables.model_validate(hermes_deliverables)

    # GIVEN Hermes parses deliverables and generates a valid response
    mocker.patch.object(HermesApi, "create_housekeeper_bundle")
    HermesApi.create_housekeeper_bundle.return_value = deliverables_response_data

    # WHEN storing the case files
    result = cli_runner.invoke(workflow_cli, [workflow, "store", case_id], obj=context)

    # THEN bundle should be successfully added to Housekeeper and StatusDB
    assert result.exit_code == EXIT_SUCCESS
    assert "Analysis successfully stored in Housekeeper" in caplog.text
    assert context.housekeeper_api.bundle(case_id)

    # THEN the analysis should be updated in StatusDB
    NfAnalysisAPI.update_analysis_as_completed_statusdb.assert_called_with(
        case_id=case_id, hk_version_id=ANY, comment=ANY, dry_run=False, force=False
    )


@pytest.mark.parametrize(
    "workflow",
    NEXTFLOW_WORKFLOWS + [Workflow.NALLO],
)
def test_store_fail(
    cli_runner: CliRunner,
    workflow: Workflow,
    real_housekeeper_api: HousekeeperAPI,
    deliverables_template_content: list[dict],
    caplog: LogCaptureFixture,
    request: FixtureRequest,
    mocker,
):
    """Test store command fails when a case did not finish for a workflow."""
    caplog.set_level(logging.INFO)
    context: CGConfig = request.getfixturevalue(f"{workflow}_context")

    # GIVEN a case id where analysis finish is not mocked
    case_id_fail: str = request.getfixturevalue(f"{workflow}_case_id")

    # GIVEN a mocked deliverables template
    mocker.patch.object(
        NfAnalysisAPI,
        "get_deliverables_template_content",
        return_value=deliverables_template_content,
    )

    # GIVEN that the Housekeeper store is empty
    context.housekeeper_api_: HousekeeperAPI = real_housekeeper_api
    context.meta_apis["analysis_api"].housekeeper_api = real_housekeeper_api

    # GIVEN that the bundle is not present in Housekeeper
    assert not context.housekeeper_api.bundle(case_id_fail)

    # WHEN running command
    result_fail = cli_runner.invoke(workflow_cli, [workflow, "store", case_id_fail], obj=context)

    # THEN bundle exist status should be
    assert result_fail.exit_code != EXIT_SUCCESS


@pytest.mark.parametrize(
    "workflow",
    NEXTFLOW_WORKFLOWS + [Workflow.NALLO],
)
def test_store_available_success(
    cli_runner: CliRunner,
    workflow: Workflow,
    real_housekeeper_api: HousekeeperAPI,
    request: FixtureRequest,
    caplog: LogCaptureFixture,
    mocker,
):
    """
    Test to ensure all parts of the compound store-available command are executed given ideal
    conditions.
    """
    caplog.set_level(logging.INFO)
    context: CGConfig = request.getfixturevalue(f"{workflow}_context")

    # GIVEN a case for which we mocked files created after a successful run
    hermes_deliverables: dict = request.getfixturevalue(f"{workflow}_hermes_deliverables")
    case_id: str = request.getfixturevalue(f"{workflow}_case_id")
    request.getfixturevalue(f"{workflow}_mock_deliverable_dir")
    request.getfixturevalue(f"{workflow}_mock_analysis_finish")

    # mock update_analysis_as_completed_statusdb so we can assert is was called
    mocker.patch.object(NfAnalysisAPI, "update_analysis_as_completed_statusdb")

    # GIVEN that the Housekeeper store is empty
    context.housekeeper_api_ = real_housekeeper_api
    context.meta_apis["analysis_api"].housekeeper_api = real_housekeeper_api

    # GIVEN that HermesAPI returns a deliverables output
    mocker.patch.object(HermesApi, "convert_deliverables")
    HermesApi.convert_deliverables.return_value = CGDeliverables.model_validate(hermes_deliverables)

    # GIVEN there is available cases to store
    context.status_db.get_case_by_internal_id(case_id).action = CaseActions.RUNNING
    context.status_db.session.commit()

    # WHEN running command
    result = cli_runner.invoke(workflow_cli, [workflow, "store-available"], obj=context)

    # THEN all expected cases are picked up for storing
    assert f"Storing deliverables for {case_id}" in caplog.text

    # THEN bundle can be found in Housekeeper
    assert context.housekeeper_api.bundle(case_id)

    # THEN command exits successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN the analysis should be updated in StatusDB
    NfAnalysisAPI.update_analysis_as_completed_statusdb.assert_called_with(
        case_id=case_id, hk_version_id=ANY, comment=ANY, dry_run=False, force=False
    )


@pytest.mark.parametrize(
    "workflow",
    NEXTFLOW_WORKFLOWS + [Workflow.NALLO],
)
def test_store_available_fail(
    cli_runner: CliRunner,
    workflow: Workflow,
    real_housekeeper_api: HousekeeperAPI,
    case_id_not_enough_reads: str,
    request: FixtureRequest,
    caplog: LogCaptureFixture,
    mocker,
):
    """
    Test that store-available picks up eligible cases and does not stop after failing to store a case.
    """
    caplog.set_level(logging.INFO)
    context: CGConfig = request.getfixturevalue(f"{workflow}_context")

    # GIVEN a case for which we mocked files created after a successful run
    hermes_deliverables: dict = request.getfixturevalue(f"{workflow}_hermes_deliverables")
    case_id: str = request.getfixturevalue(f"{workflow}_case_id")
    request.getfixturevalue(f"{workflow}_mock_deliverable_dir")
    request.getfixturevalue(f"{workflow}_mock_analysis_finish")

    # GIVEN a case where analysis finish is not mocked
    failed_case_id: str = case_id_not_enough_reads

    # GIVEN that the Housekeeper store is empty
    context.housekeeper_api_ = real_housekeeper_api
    context.meta_apis["analysis_api"].housekeeper_api = real_housekeeper_api

    # mock update_analysis_as_completed_statusdb so we can assert is was called
    mocker.patch.object(NfAnalysisAPI, "update_analysis_as_completed_statusdb")

    # GIVEN that HermesAPI returns a deliverables output
    mocker.patch.object(HermesApi, "convert_deliverables")
    HermesApi.convert_deliverables.return_value = CGDeliverables.model_validate(hermes_deliverables)

    # GIVEN there is available cases to store
    context.status_db.get_case_by_internal_id(case_id).action = CaseActions.RUNNING
    context.status_db.get_case_by_internal_id(failed_case_id).action = CaseActions.RUNNING
    context.status_db.session.commit()

    # WHEN running command
    result = cli_runner.invoke(workflow_cli, [workflow, "store-available"], obj=context)

    # THEN command should not exit successfully
    assert result.exit_code == EXIT_FAIL

    # THEN all expected cases are picked up for storing
    for case in [failed_case_id, case_id]:
        assert f"Storing deliverables for {case}" in caplog.text

    # THEN one case failed to store
    assert f"Error storing {failed_case_id}" in caplog.text

    # THEN case failing store does not have an associated Housekeeper bundle
    assert not context.housekeeper_api.bundle(failed_case_id)

    # THEN bundle can be found in Housekeeper for successful case
    assert context.housekeeper_api.bundle(case_id)

    # THEN only the analysis of the successful casae should be updated in StatusDB
    NfAnalysisAPI.update_analysis_as_completed_statusdb.assert_called_once_with(
        case_id=case_id, hk_version_id=ANY, comment=ANY, dry_run=False, force=False
    )
