import logging
from pathlib import Path

from cg.cli.workflow.balsamic.base import link

EXIT_SUCCESS = 0


def test_without_options(cli_runner, balsamic_context: dict):
    """Test command without case_id"""
    # GIVEN NO case_id
    # WHEN dry running without anything specified
    result = cli_runner.invoke(link, obj=balsamic_context)
    # THEN command should mention argument
    assert result.exit_code != EXIT_SUCCESS
    assert "Missing argument" in result.output


def test_with_missing_case(cli_runner, balsamic_context: dict, caplog):
    """Test command with invalid case to start with"""
    caplog.set_level(logging.ERROR)
    # GIVEN case_id not in database
    case_id = "soberelephant"
    assert not balsamic_context["BalsamicAnalysisAPI"].store.family(case_id)
    # WHEN running
    result = cli_runner.invoke(link, [case_id], obj=balsamic_context)
    # THEN command should NOT successfully call the command it creates
    assert result.exit_code != EXIT_SUCCESS
    # THEN ERROR log should be printed containing invalid case_id
    assert case_id in caplog.text


def test_without_samples(cli_runner, balsamic_context: dict, caplog):
    """Test command with case_id and no samples"""
    caplog.set_level(logging.ERROR)
    # GIVEN case-id
    case_id = "no_sample_case"
    # WHEN dry running with dry specified
    result = cli_runner.invoke(link, [case_id], obj=balsamic_context)
    # THEN command should print the balsamic command-string
    assert result.exit_code != EXIT_SUCCESS
    # THEN warning should be printed that no samples are found
    assert case_id in caplog.text
    assert "0" in caplog.text


def test_single_panel(balsamic_context: dict, cli_runner, caplog):
    """Test with case_id that requires SINGLE TGS analysis"""
    caplog.set_level(logging.INFO)
    # GIVEN case_id containing ONE tumor, TGS application
    case_id = "balsamic_case_tgs_single"
    # WHEN dry running
    result = cli_runner.invoke(link, [case_id], obj=balsamic_context)
    # THEN command is generated successfully
    assert result.exit_code == EXIT_SUCCESS
    # THEN log should inform us that files are linked
    assert "Linking" in caplog.text
