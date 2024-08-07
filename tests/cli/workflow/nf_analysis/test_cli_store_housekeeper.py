"""Tests CLI common methods to store deliverable files into Housekeeper for NF analyses."""

import logging
from datetime import datetime

import pytest
from _pytest.fixtures import FixtureRequest
from _pytest.logging import LogCaptureFixture
from click.testing import CliRunner
from pytest_mock import MockFixture

from cg.apps.hermes.hermes_api import HermesApi
from cg.apps.hermes.models import CGDeliverables
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.cli.workflow.base import workflow as workflow_cli
from cg.constants import EXIT_SUCCESS, Workflow
from cg.constants.constants import FileFormat
from cg.constants.nextflow import NEXTFLOW_WORKFLOWS
from cg.io.controller import WriteStream
from cg.meta.workflow.analysis import AnalysisAPI
from cg.models.cg_config import CGConfig
from cg.store.store import Store
from cg.utils import Process


@pytest.mark.parametrize(
    "workflow",
    NEXTFLOW_WORKFLOWS,
)
def test_store_housekeeper_without_options(
    cli_runner: CliRunner, workflow: Workflow, request: FixtureRequest
):
    """Test store-housekeeper for workflow without case id argument."""
    context: CGConfig = request.getfixturevalue(f"{workflow}_context")

    # GIVEN no case id

    # WHEN invoking the command without additional parameters
    result = cli_runner.invoke(workflow_cli, [workflow, "store-housekeeper"], obj=context)

    # THEN command should NOT execute successfully
    assert result.exit_code != EXIT_SUCCESS

    # THEN command should mention argument
    assert "Missing argument" in result.output


@pytest.mark.parametrize(
    "workflow",
    NEXTFLOW_WORKFLOWS,
)
def test_store_housekeeper_with_missing_case(
    cli_runner: CliRunner,
    workflow: Workflow,
    caplog: LogCaptureFixture,
    case_id_does_not_exist: str,
    request: FixtureRequest,
):
    """Test store-housekeeper for workflow with invalid case."""
    caplog.set_level(logging.ERROR)
    context: CGConfig = request.getfixturevalue(f"{workflow}_context")

    # GIVEN a case id not present in StatusDB
    assert not context.status_db.get_case_by_internal_id(internal_id=case_id_does_not_exist)

    # WHEN running the store-housekeeper command
    result = cli_runner.invoke(
        workflow_cli, [workflow, "store-housekeeper", case_id_does_not_exist], obj=context
    )

    # THEN command should NOT succeed
    assert result.exit_code != EXIT_SUCCESS

    # THEN ERROR log should be printed containing the invalid case id
    assert case_id_does_not_exist in caplog.text
    assert "could not be found" in caplog.text


@pytest.mark.parametrize(
    "workflow",
    NEXTFLOW_WORKFLOWS,
)
def test_store_housekeeper_case_not_finished(
    cli_runner: CliRunner,
    workflow: Workflow,
    caplog: LogCaptureFixture,
    request: FixtureRequest,
):
    """Test store-housekeeper for workflow using a case with an incomplete analysis."""
    caplog.set_level(logging.ERROR)
    context: CGConfig = request.getfixturevalue(f"{workflow}_context")

    # GIVEN a case id
    case_id: str = request.getfixturevalue(f"{workflow}_case_id")

    # WHEN running the store-housekeeper command
    result = cli_runner.invoke(workflow_cli, [workflow, "store-housekeeper", case_id], obj=context)

    # THEN command should NOT succeed
    assert result.exit_code != EXIT_SUCCESS

    # THEN warning should be printed that no deliverables file has been found
    assert "No deliverables file found for case" in caplog.text


@pytest.mark.parametrize(
    "workflow",
    NEXTFLOW_WORKFLOWS,
)
def test_store_housekeeper_case_with_malformed_deliverables_file(
    cli_runner,
    mocker,
    workflow: Workflow,
    caplog: LogCaptureFixture,
    request: FixtureRequest,
):
    """Test store-housekeeper command for workflow using a case with malformed deliverables output."""
    context: CGConfig = request.getfixturevalue(f"{workflow}_context")
    malformed_hermes_deliverables = request.getfixturevalue(
        f"{workflow}_malformed_hermes_deliverables"
    )

    # GIVEN that HermesAPI returns a malformed deliverables output
    mocker.patch.object(Process, "run_command")
    Process.run_command.return_value = WriteStream.write_stream_from_content(
        content=malformed_hermes_deliverables, file_format=FileFormat.JSON
    )

    # GIVEN a case id
    case_id: str = request.getfixturevalue(f"{workflow}_case_id")

    # WHEN running the store-housekeeper command
    result = cli_runner.invoke(workflow_cli, [workflow, "store-housekeeper", case_id], obj=context)

    # THEN command should NOT succeed
    assert result.exit_code != EXIT_SUCCESS
    assert "Could not store bundle in Housekeeper and StatusDB" in caplog.text


@pytest.mark.parametrize(
    "workflow",
    NEXTFLOW_WORKFLOWS,
)
def test_store_housekeeper_valid_case(
    cli_runner,
    workflow: Workflow,
    mocker,
    caplog: LogCaptureFixture,
    workflow_version: str,
    housekeeper_api: HousekeeperAPI,
    request: FixtureRequest,
):
    """Test store-housekeeper command for workflow with a valid case id."""
    caplog.set_level(logging.INFO)
    context: CGConfig = request.getfixturevalue(f"{workflow}_context")
    hermes_deliverables = request.getfixturevalue(f"{workflow}_hermes_deliverables")
    request.getfixturevalue(f"{workflow}_mock_deliverable_dir")
    store: Store = context.status_db

    # GIVEN a case id
    case_id: str = request.getfixturevalue(f"{workflow}_case_id")

    # GIVEN that case is not already stored in StatusDB
    assert not store.get_case_by_internal_id(internal_id=case_id).analyses

    # GIVEN that HermesAPI returns a deliverables output
    mocker.patch.object(HermesApi, "convert_deliverables")
    HermesApi.convert_deliverables.return_value = CGDeliverables(**hermes_deliverables)

    # WHEN running the store-housekeeper command
    result = cli_runner.invoke(workflow_cli, [workflow, "store-housekeeper", case_id], obj=context)

    # THEN a bundle should be successfully added to Housekeeper and StatusDB
    assert result.exit_code == EXIT_SUCCESS
    assert "Analysis successfully stored in Housekeeper" in caplog.text
    assert "Analysis successfully stored in StatusDB" in caplog.text
    assert store.get_case_by_internal_id(internal_id=case_id).analyses
    assert context.meta_apis["analysis_api"].housekeeper_api.bundle(case_id)

    # THEN a workflow version should be correctly stored in StatusDB
    assert (
        store.get_case_by_internal_id(internal_id=case_id).analyses[0].workflow_version
        == workflow_version
    )


@pytest.mark.parametrize(
    "workflow",
    NEXTFLOW_WORKFLOWS,
)
def test_valid_case_already_added(
    cli_runner,
    mocker,
    workflow: Workflow,
    real_housekeeper_api: HousekeeperAPI,
    caplog: LogCaptureFixture,
    request: FixtureRequest,
):
    """Test store-housekeeper command for workflow with a case already added in Housekeeper."""
    caplog.set_level(logging.INFO)
    context: CGConfig = request.getfixturevalue(f"{workflow}_context")
    hermes_deliverables = request.getfixturevalue(f"{workflow}_hermes_deliverables")
    request.getfixturevalue(f"{workflow}_mock_deliverable_dir")

    # GIVEN a case id
    case_id: str = request.getfixturevalue(f"{workflow}_case_id")

    # GIVEN a Housekeeper API
    context.housekeeper_api_: HousekeeperAPI = real_housekeeper_api
    context.meta_apis["analysis_api"].housekeeper_api = real_housekeeper_api

    # GIVEN that case is not already stored in StatusDB
    assert not context.status_db.get_case_by_internal_id(internal_id=case_id).analyses

    # GIVEN that HermesAPI returns a deliverables output
    mocker.patch.object(HermesApi, "convert_deliverables")
    HermesApi.convert_deliverables.return_value = CGDeliverables(**hermes_deliverables)

    # GIVEN a case already stored in Housekeeper with existing bundles
    result_first = cli_runner.invoke(
        workflow_cli, [workflow, "store-housekeeper", case_id], obj=context
    )

    # GIVEN that the first command executed successfully
    assert result_first.exit_code == EXIT_SUCCESS

    # WHEN running the store-housekeeper command
    result = cli_runner.invoke(workflow_cli, [workflow, "store-housekeeper", case_id], obj=context)

    # THEN command should NOT succeed
    assert result.exit_code != EXIT_SUCCESS

    # THEN user should be informed that bundle was already added
    assert "Bundle already added" in caplog.text


@pytest.mark.parametrize(
    "workflow",
    NEXTFLOW_WORKFLOWS,
)
def test_dry_run(
    cli_runner: CliRunner,
    workflow: Workflow,
    caplog: LogCaptureFixture,
    mocker: MockFixture,
    real_housekeeper_api: HousekeeperAPI,
    request: FixtureRequest,
):
    """Test dry run given a successfully finished case."""
    caplog.set_level(logging.INFO)
    context: CGConfig = request.getfixturevalue(f"{workflow}_context")
    hermes_deliverables = request.getfixturevalue(f"{workflow}_hermes_deliverables")
    request.getfixturevalue(f"{workflow}_mock_deliverable_dir")

    # GIVEN a case id
    case_id: str = request.getfixturevalue(f"{workflow}_case_id")

    # GIVEN a Housekeeper API
    context.housekeeper_api_: HousekeeperAPI = real_housekeeper_api
    context.meta_apis["analysis_api"].housekeeper_api = real_housekeeper_api

    # GIVEN that HermesAPI returns a deliverables output
    mocker.patch.object(HermesApi, "convert_deliverables")
    HermesApi.convert_deliverables.return_value = CGDeliverables(**hermes_deliverables)

    # GIVEN that case is not already stored in Housekeeper
    assert not context.housekeeper_api.bundle(case_id)

    # GIVEN that case is not already stored in StatusDB
    assert not context.status_db.get_case_by_internal_id(internal_id=case_id).analyses

    # WHEN running the store-housekeeper command with dry-run specified
    result = cli_runner.invoke(
        workflow_cli, [workflow, "store-housekeeper", case_id, "--dry-run"], obj=context
    )

    # THEN bundle should not be added to Housekeeper nor StatusDB
    assert result.exit_code == EXIT_SUCCESS
    assert "Dry-run: Housekeeper changes will not be commited" in caplog.text
    assert "Dry-run: StatusDB changes will not be commited" in caplog.text
    assert not context.housekeeper_api.bundle(case_id)
