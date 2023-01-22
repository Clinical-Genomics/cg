import logging
from pathlib import Path

import pytest
from _pytest.logging import LogCaptureFixture
from click.testing import CliRunner
from pydantic import ValidationError
from pytest_mock import MockFixture

from cg.apps.hermes.hermes_api import HermesApi
from cg.apps.hermes.models import CGDeliverables
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.cli.workflow.rnafusion.base import store_housekeeper
from cg.constants import EXIT_SUCCESS
from cg.constants.constants import FileFormat
from cg.io.controller import WriteStream
from cg.meta.workflow.rnafusion import RnafusionAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.utils import Process


def test_without_options(cli_runner: CliRunner, rnafusion_context: CGConfig):
    """Test command without case_id argument."""
    # GIVEN no case_id

    # WHEN running without anything specified
    result = cli_runner.invoke(store_housekeeper, obj=rnafusion_context)

    # THEN command should NOT execute successfully
    assert result.exit_code != EXIT_SUCCESS

    # THEN command should mention argument
    assert "Missing argument" in result.output


def test_with_missing_case(
    cli_runner: CliRunner,
    rnafusion_context: CGConfig,
    caplog: LogCaptureFixture,
    not_existing_case_id: str,
):
    """Test command with invalid case to start with."""
    caplog.set_level(logging.ERROR)

    # GIVEN case_id not in database
    assert not rnafusion_context.status_db.family(not_existing_case_id)

    # WHEN running
    result = cli_runner.invoke(store_housekeeper, [not_existing_case_id], obj=rnafusion_context)

    # THEN command should NOT successfully call the command it creates
    assert result.exit_code != EXIT_SUCCESS

    # THEN ERROR log should be printed containing invalid case_id
    assert not_existing_case_id in caplog.text
    assert "could not be found" in caplog.text


def test_case_not_finished(
    cli_runner: CliRunner,
    rnafusion_context: CGConfig,
    caplog: LogCaptureFixture,
    rnafusion_case_id: str,
):
    """Test command with case_id and config file but no analysis_finish."""
    caplog.set_level(logging.ERROR)
    # GIVEN case-id
    case_id: str = rnafusion_case_id

    # WHEN running
    result = cli_runner.invoke(store_housekeeper, [case_id], obj=rnafusion_context)

    # THEN command should NOT execute successfully
    assert result.exit_code != EXIT_SUCCESS

    # THEN warning should be printed that no analysis_finish is found
    assert "Analysis not finished" in caplog.text


def test_case_with_malformed_deliverables_file(
    cli_runner,
    mocker,
    rnafusion_context: CGConfig,
    mock_deliverable,
    malformed_hermes_deliverables: dict,
    caplog: LogCaptureFixture,
    rnafusion_case_id: str,
):
    """Test command with case_id and config file and analysis_finish but malformed deliverables output."""
    caplog.set_level(logging.WARNING)
    # GIVEN a malformed output from hermes
    analysis_api: RnafusionAnalysisAPI = rnafusion_context.meta_apis["analysis_api"]

    # GIVEN that HermesAPI returns a malformed deliverables output
    mocker.patch.object(Process, "run_command")
    Process.run_command.return_value = WriteStream.write_stream_from_content(
        content=malformed_hermes_deliverables, file_format=FileFormat.JSON
    )

    # GIVEN that the output is malformed
    with pytest.raises(ValidationError):
        analysis_api.hermes_api.convert_deliverables(
            deliverables_file=Path("a_file"), pipeline="rnafusion"
        )

        # GIVEN case-id
        case_id: str = rnafusion_case_id

        # WHEN running
        result = cli_runner.invoke(store_housekeeper, [case_id], obj=rnafusion_context)

        # THEN command should NOT execute successfully
        assert result.exit_code != EXIT_SUCCESS

        # THEN information that the file is malformed should be communicated
        assert "Deliverables file is malformed" in caplog.text
        assert "field required" in caplog.text


def test_valid_case(
    cli_runner,
    mocker,
    hermes_deliverables,
    rnafusion_context: CGConfig,
    mock_deliverable,
    mock_analysis_finish,
    caplog: LogCaptureFixture,
    rnafusion_case_id: str,
):
    caplog.set_level(logging.INFO)
    # GIVEN case-id
    case_id: str = rnafusion_case_id

    # Make sure nothing is currently stored in Housekeeper

    # Make sure  analysis not already stored in StatusDB
    assert not rnafusion_context.status_db.family(case_id).analyses

    # GIVEN that HermesAPI returns a deliverables output
    mocker.patch.object(HermesApi, "convert_deliverables")
    HermesApi.convert_deliverables.return_value = CGDeliverables(**hermes_deliverables)

    # WHEN running command
    result = cli_runner.invoke(store_housekeeper, [case_id], obj=rnafusion_context)

    # THEN bundle should be successfully added to HK and StatusDB
    assert result.exit_code == EXIT_SUCCESS
    assert "Analysis successfully stored in Housekeeper" in caplog.text
    assert "Analysis successfully stored in StatusDB" in caplog.text
    assert rnafusion_context.status_db.family(case_id).analyses
    assert rnafusion_context.meta_apis["analysis_api"].housekeeper_api.bundle(case_id)


def test_valid_case_already_added(
    cli_runner,
    mocker,
    hermes_deliverables,
    rnafusion_context: CGConfig,
    real_housekeeper_api: HousekeeperAPI,
    mock_deliverable,
    mock_analysis_finish,
    caplog: LogCaptureFixture,
    rnafusion_case_id: str,
):
    caplog.set_level(logging.INFO)
    # GIVEN case-id
    case_id: str = rnafusion_case_id

    # Make sure nothing is currently stored in Housekeeper
    rnafusion_context.housekeeper_api_: HousekeeperAPI = real_housekeeper_api
    rnafusion_context.meta_apis["analysis_api"].housekeeper_api = real_housekeeper_api

    # Make sure  analysis not already stored in ClinicalDB
    assert not rnafusion_context.status_db.family(case_id).analyses
    # GIVEN that HermesAPI returns a deliverables output
    mocker.patch.object(HermesApi, "convert_deliverables")
    HermesApi.convert_deliverables.return_value = CGDeliverables(**hermes_deliverables)

    # Ensure bundles exist by creating them first
    result_first = cli_runner.invoke(store_housekeeper, [case_id], obj=rnafusion_context)

    # GIVEN that the first command executed successfully
    assert result_first.exit_code == EXIT_SUCCESS

    # WHEN running command
    result = cli_runner.invoke(store_housekeeper, [case_id], obj=rnafusion_context)

    # THEN command should NOT execute successfully
    assert result.exit_code != EXIT_SUCCESS

    # THEN user should be informed that bundle was already added
    assert "Bundle already added" in caplog.text


def test_dry_run(
    cli_runner: CliRunner,
    rnafusion_context: CGConfig,
    mock_deliverable: None,
    mock_analysis_finish: None,
    caplog: LogCaptureFixture,
    mocker: MockFixture,
    rnafusion_case_id: str,
    hermes_deliverables: dict,
    real_housekeeper_api: HousekeeperAPI,
):
    """Test dry run given a successfully finished and delivered case."""
    caplog.set_level(logging.INFO)

    # GIVEN case-id for which we created a config file, deliverables file, and analysis_finish file
    case_id: str = rnafusion_case_id

    # Set Housekeeper to an empty real Housekeeper store
    rnafusion_context.housekeeper_api_: HousekeeperAPI = real_housekeeper_api
    rnafusion_context.meta_apis["analysis_api"].housekeeper_api = real_housekeeper_api

    # GIVEN that HermesAPI returns a deliverables output
    mocker.patch.object(HermesApi, "convert_deliverables")
    HermesApi.convert_deliverables.return_value = CGDeliverables(**hermes_deliverables)

    # Make sure the bundle was not present in hk
    assert not rnafusion_context.housekeeper_api.bundle(case_id)

    # Make sure analysis not already stored in status_db
    assert not rnafusion_context.status_db.family(case_id).analyses

    # WHEN running command
    result = cli_runner.invoke(store_housekeeper, [case_id, "--dry-run"], obj=rnafusion_context)

    # THEN bundle should not be added to HK nor STATUSDB
    assert result.exit_code == EXIT_SUCCESS
    assert "Dry-run: Housekeeper changes will not be commited" in caplog.text
    assert "Dry-run: StatusDB changes will not be commited" in caplog.text
    assert not rnafusion_context.housekeeper_api.bundle(case_id)
