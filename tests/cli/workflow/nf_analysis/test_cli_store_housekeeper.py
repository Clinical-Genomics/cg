import logging
from pathlib import Path

import pytest
from _pytest.logging import LogCaptureFixture
from click.testing import CliRunner

from cg.apps.hermes.hermes_api import HermesApi
from cg.apps.hermes.models import CGDeliverables
from cg.cli.workflow.rnafusion.base import store_housekeeper
from cg.constants import EXIT_SUCCESS
from cg.constants.constants import FileFormat
from cg.io.controller import WriteStream
from cg.models.cg_config import CGConfig
from cg.utils import Process
from cg.apps.housekeeper.hk import HousekeeperAPI
from pytest_mock import MockFixture
from cg.store.store import Store


@pytest.mark.parametrize(
    "context",
    ["rnafusion_context", "taxprofiler_context"],
)
def test_store_housekeeper_without_options(cli_runner: CliRunner, context: CGConfig, request):
    """Test store_housekeeper for workflow without case_id argument."""
    context = request.getfixturevalue(context)
    # GIVEN no case_id

    # WHEN running without anything specified
    result = cli_runner.invoke(store_housekeeper, obj=context)

    # THEN command should NOT execute successfully
    assert result.exit_code != EXIT_SUCCESS

    # THEN command should mention argument
    assert "Missing argument" in result.output


@pytest.mark.parametrize(
    "context",
    ["rnafusion_context", "taxprofiler_context"],
)
def test_store_housekeeper_with_missing_case(
    cli_runner: CliRunner,
    context: CGConfig,
    caplog: LogCaptureFixture,
    case_id_does_not_exist: str,
    request,
):
    """Test store_housekeeper for workflow with invalid case to start with."""
    caplog.set_level(logging.ERROR)
    context = request.getfixturevalue(context)

    # GIVEN case_id not in database
    assert not context.status_db.get_case_by_internal_id(internal_id=case_id_does_not_exist)

    # WHEN running
    result = cli_runner.invoke(store_housekeeper, [case_id_does_not_exist], obj=context)

    # THEN command should NOT successfully call the command it creates
    assert result.exit_code != EXIT_SUCCESS

    # THEN ERROR log should be printed containing invalid case_id
    assert case_id_does_not_exist in caplog.text
    assert "could not be found" in caplog.text


@pytest.mark.parametrize(
    ("context", "case_id"),
    [
        (
            "taxprofiler_context",
            "taxprofiler_case_id",
        ),
        (
            "rnafusion_context",
            "rnafusion_case_id",
        ),
    ],
)
def test_store_housekeeper_case_not_finished(
    cli_runner: CliRunner,
    context: CGConfig,
    caplog: LogCaptureFixture,
    case_id: str,
    request,
):
    """Test store_housekeeper for workflow with case_id and config file but no analysis_finish."""
    caplog.set_level(logging.ERROR)
    context: CGConfig = request.getfixturevalue(context)
    # GIVEN a case id
    case_id: str = request.getfixturevalue(case_id)

    # WHEN running the store-housekeeper command
    result = cli_runner.invoke(store_housekeeper, [case_id], obj=context)

    # THEN command should NOT execute successfully
    assert result.exit_code != EXIT_SUCCESS

    # THEN warning should be printed that no deliverables file has been found
    assert "No deliverables file found for case" in caplog.text


@pytest.mark.parametrize(
    ("context", "case_id", "malformed_deliverables"),
    [
        (
            "taxprofiler_context",
            "taxprofiler_case_id",
            "taxprofiler_malformed_hermes_deliverables",
        ),
        (
            "rnafusion_context",
            "rnafusion_case_id",
            "rnafusion_malformed_hermes_deliverables",
        ),
    ],
)
def test_store_housekeeper_case_with_malformed_deliverables_file(
    cli_runner,
    mocker,
    context: CGConfig,
    malformed_deliverables,
    caplog: LogCaptureFixture,
    case_id: str,
    request,
):
    """Test store_housekeeper command workflow with case_id and config file
    and analysis_finish but malformed deliverables output."""

    context: CGConfig = request.getfixturevalue(context)
    malformed_hermes_deliverables = request.getfixturevalue(malformed_deliverables)

    # GIVEN that HermesAPI returns a malformed deliverables output
    mocker.patch.object(Process, "run_command")
    Process.run_command.return_value = WriteStream.write_stream_from_content(
        content=malformed_hermes_deliverables, file_format=FileFormat.JSON
    )

    # GIVEN a case id
    case_id: str = request.getfixturevalue(case_id)

    # WHEN running the store-housekeeper command
    result = cli_runner.invoke(store_housekeeper, [case_id], obj=context)

    # THEN command should NOT execute successfully
    assert result.exit_code != EXIT_SUCCESS
    assert "Could not store bundle in Housekeeper and StatusDB" in caplog.text


@pytest.mark.parametrize(
    ("context", "case_id", "hermes_deliverables", "mock_deliverable"),
    [
        (
            "taxprofiler_context",
            "taxprofiler_case_id",
            "taxprofiler_hermes_deliverables",
            "taxprofiler_mock_deliverable_dir",
        ),
        (
            "rnafusion_context",
            "rnafusion_case_id",
            "rnafusion_hermes_deliverables",
            "rnafusion_mock_deliverable_dir",
        ),
    ],
)
def test_store_housekeeper_valid_case(
    cli_runner,
    mocker,
    hermes_deliverables,
    context: CGConfig,
    mock_deliverable,
    caplog: LogCaptureFixture,
    case_id: str,
    workflow_version: str,
    housekeeper_api: HousekeeperAPI,
    request,
):
    """Test store_housekeeper command for workflow with valid case_id."""
    caplog.set_level(logging.INFO)
    context: CGConfig = request.getfixturevalue(context)
    hermes_deliverables = request.getfixturevalue(hermes_deliverables)
    request.getfixturevalue(mock_deliverable)
    store: Store = context.status_db

    # GIVEN case-id
    case_id: str = request.getfixturevalue(case_id)

    # Make sure nothing is currently stored in Housekeeper

    # Make sure analysis not already stored in StatusDB
    assert not store.get_case_by_internal_id(internal_id=case_id).analyses

    # GIVEN that HermesAPI returns a deliverables output
    mocker.patch.object(HermesApi, "convert_deliverables")
    HermesApi.convert_deliverables.return_value = CGDeliverables(**hermes_deliverables)

    # WHEN running the store housekeeper command
    result = cli_runner.invoke(store_housekeeper, [case_id], obj=context)

    # THEN a bundle should be successfully added to HK and StatusDB
    assert result.exit_code == EXIT_SUCCESS
    assert "Analysis successfully stored in Housekeeper" in caplog.text
    assert "Analysis successfully stored in StatusDB" in caplog.text
    assert store.get_case_by_internal_id(internal_id=case_id).analyses
    assert context.meta_apis["analysis_api"].housekeeper_api.bundle(case_id)

    # THEN a workflow version should be correctly stored
    assert (
        store.get_case_by_internal_id(internal_id=case_id).analyses[0].workflow_version
        == workflow_version
    )


@pytest.mark.parametrize(
    ("context", "case_id", "hermes_deliverables", "mock_deliverable"),
    [
        (
            "taxprofiler_context",
            "taxprofiler_case_id",
            "taxprofiler_hermes_deliverables",
            "taxprofiler_mock_deliverable_dir",
        ),
        (
            "rnafusion_context",
            "rnafusion_case_id",
            "rnafusion_hermes_deliverables",
            "rnafusion_mock_deliverable_dir",
        ),
    ],
)
def test_valid_case_already_added(
    cli_runner,
    mocker,
    hermes_deliverables: dict,
    context: CGConfig,
    real_housekeeper_api: HousekeeperAPI,
    mock_deliverable: Path,
    caplog: LogCaptureFixture,
    case_id: str,
    request,
):
    """Test store_housekeeper command for workflow with case already added in Housekeeper."""
    caplog.set_level(logging.INFO)
    context: CGConfig = request.getfixturevalue(context)
    hermes_deliverables = request.getfixturevalue(hermes_deliverables)
    request.getfixturevalue(mock_deliverable)
    # GIVEN a case id
    case_id: str = request.getfixturevalue(case_id)

    # Make sure nothing is currently stored in Housekeeper
    context.housekeeper_api_: HousekeeperAPI = real_housekeeper_api
    context.meta_apis["analysis_api"].housekeeper_api = real_housekeeper_api

    # Make sure  analysis not already stored in ClinicalDB
    assert not context.status_db.get_case_by_internal_id(internal_id=case_id).analyses
    # GIVEN that HermesAPI returns a deliverables output
    mocker.patch.object(HermesApi, "convert_deliverables")
    HermesApi.convert_deliverables.return_value = CGDeliverables(**hermes_deliverables)

    # Ensure bundles exist by creating them first
    result_first = cli_runner.invoke(store_housekeeper, [case_id], obj=context)

    # GIVEN that the first command executed successfully
    assert result_first.exit_code == EXIT_SUCCESS

    # WHEN running command
    result = cli_runner.invoke(store_housekeeper, [case_id], obj=context)

    # THEN command should NOT execute successfully
    assert result.exit_code != EXIT_SUCCESS

    # THEN user should be informed that bundle was already added
    assert "Bundle already added" in caplog.text


@pytest.mark.parametrize(
    ("context", "case_id", "hermes_deliverables", "mock_deliverable"),
    [
        (
            "taxprofiler_context",
            "taxprofiler_case_id",
            "taxprofiler_hermes_deliverables",
            "taxprofiler_mock_deliverable_dir",
        ),
        (
            "rnafusion_context",
            "rnafusion_case_id",
            "rnafusion_hermes_deliverables",
            "rnafusion_mock_deliverable_dir",
        ),
    ],
)
def test_dry_run(
    cli_runner: CliRunner,
    context: CGConfig,
    mock_deliverable,
    caplog: LogCaptureFixture,
    mocker: MockFixture,
    case_id: str,
    hermes_deliverables,
    real_housekeeper_api: HousekeeperAPI,
    request,
):
    """Test dry run given a successfully finished and delivered case."""
    caplog.set_level(logging.INFO)
    context: CGConfig = request.getfixturevalue(context)
    hermes_deliverables = request.getfixturevalue(hermes_deliverables)
    request.getfixturevalue(mock_deliverable)

    # GIVEN case-id for which we created a config file, deliverables file, and analysis_finish file
    case_id: str = request.getfixturevalue(case_id)

    # Set Housekeeper to an empty real Housekeeper store
    context.housekeeper_api_: HousekeeperAPI = real_housekeeper_api
    context.meta_apis["analysis_api"].housekeeper_api = real_housekeeper_api

    # GIVEN that HermesAPI returns a deliverables output
    mocker.patch.object(HermesApi, "convert_deliverables")
    HermesApi.convert_deliverables.return_value = CGDeliverables(**hermes_deliverables)

    # Make sure the bundle was not present in hk
    assert not context.housekeeper_api.bundle(case_id)

    # Make sure analysis not already stored in status_db
    assert not context.status_db.get_case_by_internal_id(internal_id=case_id).analyses

    # WHEN running command
    result = cli_runner.invoke(store_housekeeper, [case_id, "--dry-run"], obj=context)

    # THEN bundle should not be added to HK nor STATUSDB
    assert result.exit_code == EXIT_SUCCESS
    assert "Dry-run: Housekeeper changes will not be commited" in caplog.text
    assert "Dry-run: StatusDB changes will not be commited" in caplog.text
    assert not context.housekeeper_api.bundle(case_id)
