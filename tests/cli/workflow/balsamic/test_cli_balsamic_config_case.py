"""This script tests the cli methods to create the case config for balsamic"""
import logging
from pathlib import Path

import pytest

from cg.cli.workflow.balsamic.base import config_case
from tests.cli.workflow.balsamic.conftest import balsamic_context

EXIT_SUCCESS = 0


def test_without_options(cli_runner, balsamic_context):
    """Test command with dry option"""
    # GIVEN NO case_id
    # WHEN dry running without anything specified
    result = cli_runner.invoke(config_case, obj=balsamic_context)
    # THEN command should mention argument
    assert result.exit_code != EXIT_SUCCESS
    assert "Missing argument" in result.output


def test_with_missing_case(cli_runner, balsamic_context, caplog):
    """Test command with case to start with"""
    caplog.set_level(logging.WARNING)
    # GIVEN case_id not in database
    case_id = "soberelephant"
    assert not balsamic_context["BalsamicAnalysisAPI"].store.family(case_id)
    # WHEN running
    result = cli_runner.invoke(config_case, [case_id], obj=balsamic_context)
    # THEN command should successfully call the command it creates
    assert result.exit_code != EXIT_SUCCESS
    with caplog.at_level(logging.WARNING):
        assert case_id in caplog.text


def test_dry(cli_runner, balsamic_context, caplog):
    """Test command with --dry option"""
    caplog.set_level(logging.INFO)
    # GIVEN a VALID case_id
    case_id = "balsamic_case_wgs_paired"
    # WHEN dry running with dry specified
    result = cli_runner.invoke(config_case, [case_id, "--dry-run"], obj=balsamic_context)
    # THEN command should print the balsamic command-string
    assert result.exit_code == EXIT_SUCCESS
    with caplog.at_level(logging.INFO):
        assert "balsamic" in caplog.text
        assert case_id in caplog.text


def test_target_bed(cli_runner, balsamic_context, balsamic_bed_2_path, caplog):
    """Test command with --target-bed option"""
    caplog.set_level(logging.INFO)
    # GIVEN VALID case_id of application type that requires BED
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
    caplog.set_level(logging.INFO)
    # GIVEN case that bed-version set in lims with same version existing in status db
    case_id = "balsamic_case_tgs_single"
    # WHEN dry running
    result = cli_runner.invoke(config_case, [case_id, "--dry-run"], obj=balsamic_context)
    # THEN dry-print should include the bed_key and the bed_value including path
    assert result.exit_code == EXIT_SUCCESS
    with caplog.at_level(logging.INFO):
        assert "--panel-bed" in caplog.text
        assert ".bed" in caplog.text


def test_paired_wgs(balsamic_context, cli_runner, caplog):
    caplog.set_level(logging.INFO)
    # GIVEN case_id containing ONE tumor, ONE normal, WGS application
    case_id = "balsamic_case_wgs_paired"
    # WHEN dry running
    result = cli_runner.invoke(config_case, [case_id, "--dry-run"], obj=balsamic_context)
    # THEN command is generated successfully
    assert result.exit_code == EXIT_SUCCESS
    with caplog.at_level(logging.INFO):
        # THEN dry-print should not include panel bed
        assert "--panel-bed" not in caplog.text
        # THEN tumor and normal options should be included in command
        assert "--tumor" in caplog.text
        assert "--normal" in caplog.text


def test_paired_panel(balsamic_context, cli_runner, caplog):
    caplog.set_level(logging.INFO)
    # GIVEN case_id containing ONE tumor, ONE normal, TGS application
    case_id = "balsamic_case_tgs_paired"
    # WHEN dry running
    result = cli_runner.invoke(config_case, [case_id, "--dry-run"], obj=balsamic_context)
    # THEN command is generated successfully
    assert result.exit_code == EXIT_SUCCESS
    with caplog.at_level(logging.INFO):
        # THEN dry-print should include panel bed
        assert "--panel-bed" in caplog.text
        # THEN tumor and normal options should be included in command
        assert "--tumor" in caplog.text
        assert "--normal" in caplog.text


def test_single_wgs(balsamic_context, cli_runner, caplog):
    caplog.set_level(logging.INFO)
    # GIVEN case_id containing ONE tumor, WGS application
    case_id = "balsamic_case_wgs_single"
    # WHEN dry running
    result = cli_runner.invoke(config_case, [case_id, "--dry-run"], obj=balsamic_context)
    # THEN command is generated successfully
    assert result.exit_code == EXIT_SUCCESS
    with caplog.at_level(logging.INFO):
        # THEN dry-print should not include panel bed
        assert "--panel-bed" not in caplog.text
        # THEN tumor and normal options should be included in command
        assert "--tumor" in caplog.text
        assert "--normal" not in caplog.text


def test_single_wgs_panel_arg(balsamic_context, cli_runner, caplog):
    caplog.set_level(logging.WARNING)
    # GIVEN case_id containing ONE tumor, WGS application and panel bed argument
    case_id = "balsamic_case_wgs_single"
    panel_bed = "balsamic_bed_1.bed"
    # WHEN dry running
    result = cli_runner.invoke(
        config_case, [case_id, "--dry-run", "--panel-bed", panel_bed], obj=balsamic_context
    )
    # THEN command is NOT generated successfully
    assert result.exit_code != EXIT_SUCCESS
    # THEN log warning should be printed
    with caplog.at_level(logging.WARNING):
        assert "Could not create config" in caplog.text


def test_single_panel(balsamic_context, cli_runner, caplog):
    caplog.set_level(logging.INFO)
    # GIVEN case_id containing ONE tumor, TGS application
    case_id = "balsamic_case_tgs_single"
    # WHEN dry running
    result = cli_runner.invoke(config_case, [case_id, "--dry-run"], obj=balsamic_context)
    # THEN command is generated successfully
    assert result.exit_code == EXIT_SUCCESS
    with caplog.at_level(logging.INFO):
        # THEN dry-print should include panel bed
        assert "--panel-bed" in caplog.text
        # THEN tumor and normal options should be included in command
        assert "--tumor" in caplog.text
        assert "--normal" not in caplog.text


def test_error_normal_only(balsamic_context, cli_runner, caplog):
    caplog.set_level(logging.WARNING)
    # GIVEN case_id containing ONE normal, WGS application
    case_id = "balsamic_case_tgs_single_error"
    # WHEN dry running
    result = cli_runner.invoke(config_case, [case_id, "--dry-run"], obj=balsamic_context)
    # THEN command is NOT generated successfully
    assert result.exit_code != EXIT_SUCCESS
    # THEN log warning should be printed
    with caplog.at_level(logging.WARNING):
        assert "Could not create config" in caplog.text


def test_error_two_tumor(balsamic_context, cli_runner, caplog):
    caplog.set_level(logging.WARNING)
    # GIVEN case_id containing TWO tumor, ONE normal, TGS application
    case_id = "balsamic_case_tgs_paired_error"
    # WHEN dry running
    result = cli_runner.invoke(config_case, [case_id, "--dry-run"], obj=balsamic_context)
    # THEN command is NOT generated successfully
    assert result.exit_code != EXIT_SUCCESS
    # THEN log warning should be printed
    with caplog.at_level(logging.WARNING):
        assert "Could not create config" in caplog.text


def test_error_mixed_application(balsamic_context, cli_runner, caplog):
    caplog.set_level(logging.WARNING)
    case_id = "balsamic_case_mixed_paired_error"
    # WHEN dry running
    result = cli_runner.invoke(config_case, [case_id, "--dry-run"], obj=balsamic_context)
    # THEN command is NOT generated successfully
    assert result.exit_code != EXIT_SUCCESS
    # THEN log warning should be printed
    with caplog.at_level(logging.WARNING):
        assert "Could not create config" in caplog.text


def test_error_not_balsamic_application(balsamic_context, cli_runner, caplog):
    caplog.set_level(logging.WARNING)
    case_id = "balsamic_case_mixed_wgs_mic_paired_error"
    # WHEN dry running
    result = cli_runner.invoke(config_case, [case_id, "--dry-run"], obj=balsamic_context)
    # THEN command is NOT generated successfully
    assert result.exit_code != EXIT_SUCCESS
    # THEN log warning should be printed
    with caplog.at_level(logging.WARNING):
        assert "Could not create config" in caplog.text


def test_error_mixed_panel_bed(balsamic_context, cli_runner, caplog):
    caplog.set_level(logging.WARNING)
    case_id = "balsamic_case_mixed_bed_paired_error"
    # WHEN dry running
    result = cli_runner.invoke(config_case, [case_id, "--dry-run"], obj=balsamic_context)
    # THEN command is NOT generated successfully
    assert result.exit_code != EXIT_SUCCESS
    # THEN log warning should be printed
    with caplog.at_level(logging.WARNING):
        assert "Could not create config" in caplog.text


def test_error_mixed_panel_bed_resque(balsamic_context, cli_runner, caplog):
    caplog.set_level(logging.INFO)
    # GIVEN case_id with mixed panel_bed in LIMS and a panel bed argument
    case_id = "balsamic_case_mixed_bed_paired_error"
    panel_bed = "balsamic_bed_1.bed"
    # WHEN dry running
    result = cli_runner.invoke(
        config_case, [case_id, "--dry-run", "--panel-bed", panel_bed], obj=balsamic_context
    )
    # THEN command is generated successfully
    assert result.exit_code == EXIT_SUCCESS
    # THEN panel bed should be present in command
    with caplog.at_level(logging.INFO):
        assert "--panel-bed" in caplog.text
        assert panel_bed in caplog.text


def test_error_only_mip_tumor(balsamic_context, cli_runner, caplog):
    caplog.set_level(logging.WARNING)
    case_id = "mip_case_wgs_single"
    # WHEN dry running
    result = cli_runner.invoke(config_case, [case_id, "--dry-run"], obj=balsamic_context)
    # THEN command is NOT generated successfully
    assert result.exit_code != EXIT_SUCCESS
    # THEN log warning should be printed
    with caplog.at_level(logging.WARNING):
        assert "Could not create config" in caplog.text
        assert "no samples tagged for BALSAMIC analysis" in caplog.text
