"""This script tests the cli methods to create the case config for balsamic"""
import logging
from pathlib import Path

import pytest

from cg.cli.workflow.balsamic.base import config_case
from tests.cli.workflow.balsamic.conftest import balsamic_context

EXIT_SUCCESS = 0


def test_without_options(cli_runner, balsamic_context):
    """Test command with dry option"""

    # GIVEN

    # WHEN dry running without anything specified
    result = cli_runner.invoke(config_case, obj=balsamic_context)

    # THEN command should mention argument
    assert result.exit_code != EXIT_SUCCESS
    assert "Missing argument" in result.output


def test_with_missing_case(cli_runner, balsamic_context, caplog):
    """Test command with case to start with"""

    # GIVEN case-id not in database
    case_id = "soberelephant"

    assert not balsamic_context["BalsamicAnalysisAPI"].store.family(case_id)
    caplog.set_level(logging.WARNING)

    # WHEN running
    result = cli_runner.invoke(config_case, [case_id], obj=balsamic_context)

    # THEN command should successfully call the command it creates
    assert result.exit_code != EXIT_SUCCESS
    with caplog.at_level(logging.WARNING):
        assert case_id in caplog.text


def test_dry(cli_runner, balsamic_context, caplog):
    """Test command with --dry option"""

    # GIVEN VALID CASE_ID
    case_id = "balsamic_case_wgs_paired"
    caplog.set_level(logging.INFO)

    # WHEN dry running with dry specified
    result = cli_runner.invoke(config_case, [case_id, "--dry-run"], obj=balsamic_context)
    # THEN command should print the balsamic command-string
    assert result.exit_code == EXIT_SUCCESS
    with caplog.at_level(logging.INFO):
        assert "balsamic" in caplog.text
        assert case_id in caplog.text


def test_target_bed(cli_runner, balsamic_context, balsamic_bed_2_path, caplog):
    """Test command with --target-bed option"""

    # GIVEN VALID case-id
    caplog.set_level(logging.INFO)
    case_id = "balsamic_case_tgs_single"
    option_key = "--panel-bed"
    option_value = balsamic_bed_2_path

    # WHEN dry running with option specified
    result = cli_runner.invoke(
        config_case, [case_id, "--dry-run", option_key, option_value], obj=balsamic_context,
    )
    # THEN dry-print should include the the option-value
    assert result.exit_code == EXIT_SUCCESS
    with caplog.at_level(logging.INFO):
        assert option_key in caplog.text
        assert option_value in caplog.text


def test_target_bed_from_lims(cli_runner, balsamic_context, caplog):
    """Test command without --target-bed option"""

    # GIVEN case that bed-version set in lims with same version existing in status db
    caplog.set_level(logging.INFO)
    case_id = "balsamic_case_tgs_single"

    # WHEN dry running
    result = cli_runner.invoke(config_case, [case_id, "--dry-run"], obj=balsamic_context)

    # THEN dry-print should include the bed_key and the bed_value including path
    assert result.exit_code == EXIT_SUCCESS
    with caplog.at_level(logging.INFO):
        assert "--panel-bed" in caplog.text
        assert ".bed" in caplog.text


def test_paired_wgs():
    pass


def test_paired_panel():
    pass


def test_single_wgs():
    pass


def test_single_panel():
    pass


def test_error_normal_only():
    pass


def test_error_two_tumor():
    pass


def test_error_mixed_application():
    pass


def test_error_not_balsamic_application():
    pass


def test_error_mixed_panel_bed():
    pass


def test_error_only_mip_tumor():
    pass
