import json
import logging
from pathlib import Path

import pytest
from pydantic import ValidationError

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.cli.workflow.balsamic.base import store_housekeeper
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI

EXIT_SUCCESS = 0


def test_without_options(cli_runner, balsamic_context: dict):
    """Test command without case_id argument"""
    # GIVEN no case_id

    # WHEN dry running without anything specified
    result = cli_runner.invoke(store_housekeeper, obj=balsamic_context)

    # THEN command should NOT execute successfully
    assert result.exit_code != EXIT_SUCCESS

    # THEN command should mention argument
    assert "Missing argument" in result.output


def test_with_missing_case(cli_runner, balsamic_context: dict, caplog):
    """Test command with invalid case to start with"""
    caplog.set_level(logging.ERROR)

    # GIVEN case_id not in database
    case_id = "soberelephant"
    assert not balsamic_context["BalsamicAnalysisAPI"].store.family(case_id)

    # WHEN running
    result = cli_runner.invoke(store_housekeeper, [case_id], obj=balsamic_context)

    # THEN command should NOT successfully call the command it creates
    assert result.exit_code != EXIT_SUCCESS

    # THEN ERROR log should be printed containing invalid case_id
    assert case_id in caplog.text
    assert "not found" in caplog.text


def test_without_samples(cli_runner, balsamic_context: dict, caplog):
    """Test command with case_id and no samples"""
    caplog.set_level(logging.ERROR)
    # GIVEN case-id
    case_id = "no_sample_case"

    # WHEN dry running with dry specified
    result = cli_runner.invoke(store_housekeeper, [case_id], obj=balsamic_context)

    # THEN command should NOT execute successfully
    assert result.exit_code != EXIT_SUCCESS

    # THEN warning should be printed that no config file is found
    assert "0" in caplog.text


def test_without_config(cli_runner, balsamic_context: dict, caplog):
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
    cli_runner, balsamic_context: dict, mock_config: dict, caplog
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
    balsamic_context: dict,
    mock_config: dict,
    mock_deliverable,
    malformed_hermes_deliverables: dict,
    caplog,
):
    """Test command with case_id and config file and analysis_finish but malformed deliverables output"""
    caplog.set_level(logging.WARNING)
    # GIVEN a malformed output from hermes
    analysis_api: BalsamicAnalysisAPI = balsamic_context["BalsamicAnalysisAPI"]
    analysis_api.hermes_api.process.set_stdout(text=json.dumps(malformed_hermes_deliverables))

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
    balsamic_context: dict,
    real_housekeeper_api: HousekeeperAPI,
    mock_config,
    mock_deliverable,
    caplog,
):
    caplog.set_level(logging.INFO)
    # GIVEN case-id
    case_id = "balsamic_case_wgs_single"

    # Make sure nothing is currently stored in Housekeeper
    balsamic_context["BalsamicAnalysisAPI"].housekeeper_api = real_housekeeper_api

    # Make sure  analysis not alredy stored in ClinicalDB
    assert not balsamic_context["BalsamicAnalysisAPI"].store.family(case_id).analyses

    # WHEN running command
    result = cli_runner.invoke(store_housekeeper, [case_id], obj=balsamic_context)

    # THEN bundle should be successfully added to HK and STATUS
    assert result.exit_code == EXIT_SUCCESS
    assert "Analysis successfully stored in Housekeeper" in caplog.text
    assert "Analysis successfully stored in ClinicalDB" in caplog.text
    assert balsamic_context["BalsamicAnalysisAPI"].store.family(case_id).analyses
    assert balsamic_context["BalsamicAnalysisAPI"].housekeeper_api.bundle(case_id)


def test_valid_case_already_added(
    cli_runner,
    balsamic_context: dict,
    real_housekeeper_api: HousekeeperAPI,
    mock_config,
    mock_deliverable,
    mock_analysis_finish,
    caplog,
):
    caplog.set_level(logging.ERROR)
    # GIVEN case-id
    case_id = "balsamic_case_wgs_single"

    # Make sure nothing is currently stored in Housekeeper
    balsamic_context["BalsamicAnalysisAPI"].housekeeper_api = real_housekeeper_api

    # Make sure  analysis not alredy stored in ClinicalDB
    assert not balsamic_context["BalsamicAnalysisAPI"].store.family(case_id).analyses

    # Ensure bundles exist by creating them first
    cli_runner.invoke(store_housekeeper, [case_id], obj=balsamic_context)

    # WHEN running command
    result = cli_runner.invoke(store_housekeeper, [case_id], obj=balsamic_context)

    # THEN command should NOT execute successfully
    assert result.exit_code != EXIT_SUCCESS

    # THEN user should be informed that bundle was already added
    assert "Bundle already added" in caplog.text
