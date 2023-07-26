import logging
from pathlib import Path

import pytest
from cg.apps.hermes.hermes_api import HermesApi
from cg.apps.hermes.models import CGDeliverables
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.cli.workflow.balsamic.base import store_housekeeper
from cg.constants import EXIT_SUCCESS
from cg.constants.constants import FileFormat
from cg.io.controller import WriteStream
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.utils import Process
from click.testing import CliRunner
from pydantic.v1 import ValidationError


def test_without_options(cli_runner: CliRunner, balsamic_context: CGConfig):
    """Test command without case_id argument"""
    # GIVEN no case_id

    # WHEN dry running without anything specified
    result = cli_runner.invoke(store_housekeeper, obj=balsamic_context)

    # THEN command should NOT execute successfully
    assert result.exit_code != EXIT_SUCCESS

    # THEN command should mention argument
    assert "Missing argument" in result.output


def test_with_missing_case(cli_runner: CliRunner, balsamic_context: CGConfig, caplog):
    """Test command with invalid case to start with"""
    caplog.set_level(logging.ERROR)

    # GIVEN case_id not in database
    case_id = "soberelephant"
    assert not balsamic_context.status_db.get_case_by_internal_id(internal_id=case_id)

    # WHEN running
    result = cli_runner.invoke(store_housekeeper, [case_id], obj=balsamic_context)

    # THEN command should NOT successfully call the command it creates
    assert result.exit_code != EXIT_SUCCESS

    # THEN ERROR log should be printed containing invalid case_id
    assert case_id in caplog.text
    assert "could not be found" in caplog.text


def test_without_config(cli_runner: CliRunner, balsamic_context: CGConfig, caplog):
    """Test command with case_id and no config file"""
    caplog.set_level(logging.ERROR)
    # GIVEN case-id
    case_id = "balsamic_case_wgs_single"

    # WHEN dry running with dry specified
    result = cli_runner.invoke(store_housekeeper, [case_id], obj=balsamic_context)

    # THEN command should NOT execute successfully
    assert result.exit_code != EXIT_SUCCESS

    # THEN warning should be printed that no config file is found
    assert "No config file found" in caplog.text


def test_case_without_deliverables_file(
    cli_runner: CliRunner, balsamic_context: CGConfig, mock_config, caplog
):
    """Test command with case_id and config file but no analysis_finish"""
    caplog.set_level(logging.ERROR)
    # GIVEN case-id
    case_id = "balsamic_case_wgs_single"

    # WHEN dry running with dry specified
    result = cli_runner.invoke(store_housekeeper, [case_id], obj=balsamic_context)

    # THEN command should NOT execute successfully
    assert result.exit_code != EXIT_SUCCESS

    # THEN warning should be printed that no analysis_finish is found
    assert "No deliverables file found" in caplog.text


def test_case_with_malformed_deliverables_file(
    cli_runner,
    mocker,
    balsamic_context: CGConfig,
    malformed_hermes_deliverables: dict,
    caplog,
):
    """Test command with case_id and config file and analysis_finish but malformed deliverables output"""
    caplog.set_level(logging.WARNING)
    # GIVEN a malformed output from hermes
    analysis_api: BalsamicAnalysisAPI = balsamic_context.meta_apis["analysis_api"]

    # GIVEN that HermesAPI returns a malformed deliverables output
    mocker.patch.object(Process, "run_command")
    Process.run_command.return_value = WriteStream.write_stream_from_content(
        content=malformed_hermes_deliverables, file_format=FileFormat.JSON
    )

    # GIVEN that the output is malformed
    with pytest.raises(ValidationError):
        analysis_api.hermes_api.convert_deliverables(
            deliverables_file=Path("a_file"), pipeline="balsamic"
        )

        # GIVEN case-id
        case_id = "balsamic_case_wgs_single"

        # WHEN dry running with dry specified
        result = cli_runner.invoke(store_housekeeper, [case_id], obj=balsamic_context)

        # THEN command should NOT execute successfully
        assert result.exit_code != EXIT_SUCCESS

        # THEN information that the file is malformed should be communicated
        assert "Deliverables file is malformed" in caplog.text
        assert "field required" in caplog.text


def test_valid_case(
    cli_runner,
    mocker,
    hermes_deliverables,
    balsamic_context: CGConfig,
    mock_config,
    mock_deliverable,
    caplog,
):
    caplog.set_level(logging.INFO)
    # GIVEN case-id
    case_id = "balsamic_case_wgs_single"

    # Make sure nothing is currently stored in Housekeeper

    # Make sure  analysis not alredy stored in ClinicalDB
    assert not balsamic_context.status_db.get_case_by_internal_id(internal_id=case_id).analyses

    # GIVEN that HermesAPI returns a deliverables output
    mocker.patch.object(HermesApi, "convert_deliverables")
    HermesApi.convert_deliverables.return_value = CGDeliverables(**hermes_deliverables)

    # WHEN running command
    result = cli_runner.invoke(store_housekeeper, [case_id], obj=balsamic_context)

    # THEN bundle should be successfully added to HK and STATUS
    assert result.exit_code == EXIT_SUCCESS
    assert "Analysis successfully stored in Housekeeper" in caplog.text
    assert "Analysis successfully stored in StatusDB" in caplog.text
    assert balsamic_context.status_db.get_case_by_internal_id(internal_id=case_id).analyses
    assert balsamic_context.meta_apis["analysis_api"].housekeeper_api.bundle(case_id)


def test_valid_case_already_added(
    cli_runner,
    mocker,
    hermes_deliverables,
    balsamic_context: CGConfig,
    real_housekeeper_api: HousekeeperAPI,
    mock_config,
    mock_deliverable,
    caplog,
):
    caplog.set_level(logging.ERROR)
    # GIVEN case-id
    case_id = "balsamic_case_wgs_single"

    # Make sure nothing is currently stored in Housekeeper
    balsamic_context.housekeeper_api_ = real_housekeeper_api
    balsamic_context.meta_apis["analysis_api"].housekeeper_api = real_housekeeper_api

    # Make sure  analysis not already stored in ClinicalDB
    assert not balsamic_context.status_db.get_case_by_internal_id(internal_id=case_id).analyses

    # GIVEN that HermesAPI returns a deliverables output
    mocker.patch.object(HermesApi, "convert_deliverables")
    HermesApi.convert_deliverables.return_value = CGDeliverables(**hermes_deliverables)

    # Ensure bundles exist by creating them first
    cli_runner.invoke(store_housekeeper, [case_id], obj=balsamic_context)

    # WHEN running command
    result = cli_runner.invoke(store_housekeeper, [case_id], obj=balsamic_context)

    # THEN command should NOT execute successfully
    assert result.exit_code != EXIT_SUCCESS

    # THEN user should be informed that bundle was already added
    assert "Bundle already added" in caplog.text
