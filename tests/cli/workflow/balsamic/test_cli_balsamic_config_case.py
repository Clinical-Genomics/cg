"""Tests cli methods to create the case config for balsamic"""

import logging
from pathlib import Path

import pytest
from _pytest.logging import LogCaptureFixture

from cg.cli.workflow.balsamic.base import config_case
from click.testing import CliRunner

from cg.exc import BalsamicStartError
from cg.models.cg_config import CGConfig

EXIT_SUCCESS = 0


def test_without_options(cli_runner: CliRunner, balsamic_context: CGConfig):
    """Test command without case_id."""
    # GIVEN NO case_id
    # WHEN dry running without anything specified
    result = cli_runner.invoke(config_case, obj=balsamic_context)
    # THEN command should mention argument
    assert result.exit_code != EXIT_SUCCESS
    assert "Missing argument" in result.output


def test_with_missing_case(
    cli_runner: CliRunner, balsamic_context: CGConfig, caplog: LogCaptureFixture
):
    """Test command with invalid case to start with."""
    caplog.set_level(logging.ERROR)
    # GIVEN case_id not in database
    case_id = "soberelephant"
    assert not balsamic_context.status_db.family(case_id)
    # WHEN running
    result = cli_runner.invoke(config_case, [case_id], obj=balsamic_context)
    # THEN command should NOT successfully call the command it creates
    assert result.exit_code != EXIT_SUCCESS
    # THEN ERROR log should be printed containing invalid case_id
    assert "could not be found in StatusDB!" in caplog.text


def test_without_samples(
    cli_runner: CliRunner, balsamic_context: CGConfig, caplog: LogCaptureFixture
):
    """Test command with case_id and no samples."""
    caplog.set_level(logging.ERROR)
    # GIVEN case-id
    case_id = "no_sample_case"
    # WHEN dry running with dry specified
    result = cli_runner.invoke(config_case, [case_id, "--dry-run"], obj=balsamic_context)
    # THEN command should print the balsamic command-string
    assert result.exit_code != EXIT_SUCCESS
    # THEN warning should be printed that no config file is found
    assert case_id in caplog.text
    assert "has no samples" in caplog.text


def test_dry(cli_runner: CliRunner, balsamic_context: CGConfig, caplog: LogCaptureFixture):
    """Test command with --dry option."""
    caplog.set_level(logging.INFO)
    # GIVEN a VALID case_id
    case_id = "balsamic_case_wgs_paired"
    # WHEN dry running with dry option specified
    result = cli_runner.invoke(config_case, [case_id, "--dry-run"], obj=balsamic_context)
    # THEN command should print the balsamic command string
    assert result.exit_code == EXIT_SUCCESS
    # THEN gry run, balsamic and case_id should be in log
    assert "Dry run" in caplog.text
    assert "balsamic" in caplog.text
    assert case_id in caplog.text


def test_genome_version(
    cli_runner: CliRunner, balsamic_context: CGConfig, caplog: LogCaptureFixture
):
    """Test command with --genome-version option."""
    caplog.set_level(logging.INFO)
    # GIVEN a VALID case_id and genome_version
    case_id = "balsamic_case_wgs_paired"
    option_key = "--genome-version"
    option_value = "canfam3"
    # WHEN dry running with genome option specified
    result = cli_runner.invoke(
        config_case,
        [case_id, "--dry-run", option_key, option_value],
        obj=balsamic_context,
    )
    # THEN command should be generated successfully
    assert result.exit_code == EXIT_SUCCESS
    # THEN dry-print should include the option key and value
    assert option_key in caplog.text
    assert option_value in caplog.text


def test_target_bed(
    cli_runner: CliRunner,
    balsamic_context: CGConfig,
    balsamic_bed_2_path: Path,
    caplog: LogCaptureFixture,
):
    """Test command with --panel-bed option."""
    caplog.set_level(logging.INFO)
    # GIVEN VALID case_id of application type that requires BED
    case_id = "balsamic_case_tgs_single"
    option_key = "--panel-bed"
    option_value = balsamic_bed_2_path
    # WHEN dry running with PANEL BED option specified
    result = cli_runner.invoke(
        config_case,
        [case_id, "--dry-run", option_key, option_value],
        obj=balsamic_context,
    )
    # THEN command should be generated successfully
    assert result.exit_code == EXIT_SUCCESS
    # THEN dry-print should include the the option key and value
    assert option_key in caplog.text
    assert option_value in caplog.text


def test_target_bed_from_lims(
    cli_runner: CliRunner, balsamic_context: CGConfig, caplog: LogCaptureFixture
):
    """Test command without --target-bed option when BED can be retrieved from LIMS."""
    caplog.set_level(logging.INFO)
    # GIVEN case that bed-version set in lims with same version existing in status db
    case_id = "balsamic_case_tgs_single"
    # WHEN dry running
    result = cli_runner.invoke(config_case, [case_id, "--dry-run"], obj=balsamic_context)
    # THEN command should be generated successfully
    assert result.exit_code == EXIT_SUCCESS
    # THEN dry-print should include the bed_key and the bed_value including path
    assert "--panel-bed" in caplog.text
    assert ".bed" in caplog.text


def test_paired_wgs(balsamic_context: CGConfig, cli_runner: CliRunner, caplog: LogCaptureFixture):
    """Test with case_id that requires PAIRED WGS analysis."""
    caplog.set_level(logging.INFO)
    # GIVEN case_id containing ONE tumor, ONE normal, WGS application
    case_id = "balsamic_case_wgs_paired"
    # WHEN dry running
    result = cli_runner.invoke(config_case, [case_id, "--dry-run"], obj=balsamic_context)
    # THEN command is generated successfully
    assert result.exit_code == EXIT_SUCCESS
    # THEN dry-print should not include panel bed
    assert "--panel-bed" not in caplog.text
    # THEN tumor and normal options should be included in command
    assert "--tumor" in caplog.text
    assert "--normal" in caplog.text


def test_paired_panel(balsamic_context: CGConfig, cli_runner: CliRunner, caplog: LogCaptureFixture):
    """Test with case_id that requires PAIRED TGS analysis."""
    caplog.set_level(logging.INFO)
    # GIVEN case_id containing ONE tumor, ONE normal, TGS application
    case_id = "balsamic_case_tgs_paired"
    # WHEN dry running
    result = cli_runner.invoke(config_case, [case_id, "--dry-run"], obj=balsamic_context)
    # THEN command is generated successfully
    assert result.exit_code == EXIT_SUCCESS
    # THEN dry-print should include panel bed
    assert "--panel-bed" in caplog.text
    # THEN tumor and normal options should be included in command
    assert "--tumor" in caplog.text
    assert "--normal" in caplog.text


def test_pon_cnn(
    balsamic_context: CGConfig,
    cli_runner: CliRunner,
    balsamic_bed_1_path: str,
    balsamic_pon_1_path: str,
    caplog: LogCaptureFixture,
):
    """Test command with --pon-cnn option."""
    caplog.set_level(logging.INFO)
    # GIVEN VALID case_id of application with BED and PoN files
    case_id = "balsamic_case_tgs_paired"
    panel_key = "--panel-bed"
    panel_value = balsamic_bed_1_path
    pon_key = "--pon-cnn"
    pon_value = balsamic_pon_1_path
    # WHEN dry running with PANEL BED and PON CNN options specified
    result = cli_runner.invoke(
        config_case,
        [case_id, "--dry-run", panel_key, panel_value, pon_key, pon_value],
        obj=balsamic_context,
    )
    # THEN command should be generated successfully
    assert result.exit_code == EXIT_SUCCESS
    # THEN dry-print should include the PoN option key and value
    assert pon_key in caplog.text
    assert pon_value in caplog.text


def test_single_wgs(balsamic_context: CGConfig, cli_runner: CliRunner, caplog: LogCaptureFixture):
    """Test with case_id that requires SINGLE WGS analysis."""
    caplog.set_level(logging.INFO)
    # GIVEN case_id containing ONE tumor, WGS application
    case_id = "balsamic_case_wgs_single"
    # WHEN dry running
    result = cli_runner.invoke(config_case, [case_id, "--dry-run"], obj=balsamic_context)
    # THEN command is generated successfully
    assert result.exit_code == EXIT_SUCCESS
    # THEN dry-print should NOT include panel bed
    assert "--panel-bed" not in caplog.text
    # THEN tumor option should be included in command
    assert "--tumor" in caplog.text
    # THEN normal option should NOT be included in command
    assert "--normal" not in caplog.text


def test_single_panel(balsamic_context: CGConfig, cli_runner: CliRunner, caplog: LogCaptureFixture):
    """Test with case_id that requires SINGLE TGS analysis."""
    caplog.set_level(logging.INFO)
    # GIVEN case_id containing ONE tumor, TGS application
    case_id = "balsamic_case_tgs_single"
    # WHEN dry running
    result = cli_runner.invoke(config_case, [case_id, "--dry-run"], obj=balsamic_context)
    # THEN command is generated successfully
    assert result.exit_code == EXIT_SUCCESS
    # THEN dry-print should include panel bed
    assert "--panel-bed" in caplog.text
    # THEN tumor option should be included in command
    assert "--tumor" in caplog.text
    # THEN normal option should NOT be included in command
    assert "--normal" not in caplog.text


def test_error_single_wgs_panel_arg(
    balsamic_context: CGConfig, cg_dir: Path, cli_runner: CliRunner, caplog: LogCaptureFixture
):
    """Test with case_id that requires SINGLE WGS analysis and --panel-bed argument."""
    caplog.set_level(logging.ERROR)
    # GIVEN case_id containing ONE tumor, WGS application and panel bed argument
    case_id = "balsamic_case_wgs_single"
    panel_bed = Path(cg_dir, "balsamic_bed_1.bed")
    # WHEN dry running
    result = cli_runner.invoke(
        config_case,
        [case_id, "--dry-run", "--panel-bed", panel_bed],
        obj=balsamic_context,
    )
    # THEN command is NOT generated successfully
    assert result.exit_code != EXIT_SUCCESS
    # THEN log warning not to set panel for WGS should be printed
    assert "Cannot set panel_bed for WGS sample" in caplog.text


def test_error_normal_only(
    balsamic_context: CGConfig, cli_runner: CliRunner, caplog: LogCaptureFixture
):
    """Test with case_id that has only one NORMAL sample."""
    caplog.set_level(logging.WARNING)

    # GIVEN case_id containing one normal sample
    case_id = "balsamic_case_tgs_single_error"

    # WHEN dry running
    result = cli_runner.invoke(config_case, [case_id, "--dry-run"], obj=balsamic_context)

    # THEN a start case error should be raised
    assert result.exit_code != EXIT_SUCCESS
    assert (
        f"Case {case_id} only has a normal sample. Use the --force-normal flag to treat it as a tumor."
        in caplog.text
    )


def test_normal_only_force_flag(
    balsamic_context: CGConfig, cli_runner: CliRunner, caplog: LogCaptureFixture
):
    """Test with case_id that has only one NORMAL sample but the run is forced."""
    caplog.set_level(logging.WARNING)

    # GIVEN case_id containing one normal sample
    case_id = "balsamic_case_tgs_single_error"

    # WHEN dry running
    result = cli_runner.invoke(
        config_case, [case_id, "--dry-run", "--force-normal"], obj=balsamic_context
    )

    # THEN command should be generated successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN a warning log should be printed specifying that a normal sample will be used as tumor for Balsamic analysis
    assert (
        f"Only a normal sample was found for case {case_id}. Balsamic analysis will treat it as a tumor sample."
        in caplog.text
    )


def test_error_two_tumor(
    balsamic_context: CGConfig, cli_runner: CliRunner, caplog: LogCaptureFixture
):
    """Test with case_id that requires WGS analysis but has TWO tumor ONE normal samples."""
    caplog.set_level(logging.ERROR)
    # GIVEN case_id containing TWO tumor, ONE normal, TGS application
    case_id = "balsamic_case_tgs_paired_error"
    # WHEN dry running
    result = cli_runner.invoke(config_case, [case_id, "--dry-run"], obj=balsamic_context)
    # THEN command is NOT generated successfully
    assert result.exit_code != EXIT_SUCCESS
    # THEN log warning should be printed
    assert f"Case {case_id} has an invalid number of samples" in caplog.text


def test_error_mixed_application(
    balsamic_context: CGConfig, cli_runner: CliRunner, caplog: LogCaptureFixture
):
    """Test with case_id that has ONE tumor ONE normal samples marked for WGS and TGS analysis."""
    caplog.set_level(logging.ERROR)
    case_id = "balsamic_case_mixed_paired_error"
    # WHEN dry running
    result = cli_runner.invoke(config_case, [case_id, "--dry-run"], obj=balsamic_context)
    # THEN command is NOT generated successfully
    assert result.exit_code != EXIT_SUCCESS
    # THEN log warning should be printed
    assert "Multiple application types found" in caplog.text


def test_error_not_balsamic_application(
    balsamic_context: CGConfig, cli_runner: CliRunner, caplog: LogCaptureFixture
):
    """Test with case_id that has PAIRED samples marked for WGS and MIC analysis."""
    caplog.set_level(logging.ERROR)
    case_id = "balsamic_case_mixed_wgs_mic_paired_error"
    # WHEN dry running
    result = cli_runner.invoke(config_case, [case_id, "--dry-run"], obj=balsamic_context)
    # THEN command is NOT generated successfully
    assert result.exit_code != EXIT_SUCCESS
    # THEN log warning should be printed
    assert "not compatible with BALSAMIC" in caplog.text


def test_error_mixed_panel_bed_resque(
    balsamic_context: CGConfig, cli_runner: CliRunner, caplog: LogCaptureFixture
):
    """
    Test with case_id marked for PAIRED TGS analysis but different BED files in LIMS
    and supplying --panel-bed option should prevent error.
    """
    caplog.set_level(logging.INFO)
    # GIVEN case_id with mixed panel_bed in LIMS and a panel bed argument
    case_id = "balsamic_case_mixed_bed_paired_error"
    panel_bed = "BalsamicBed1"
    # WHEN dry running
    result = cli_runner.invoke(
        config_case,
        [case_id, "--dry-run", "--panel-bed", panel_bed],
        obj=balsamic_context,
    )
    # THEN command is generated successfully
    assert result.exit_code == EXIT_SUCCESS
    # THEN panel bed should override LIMS data and be present in command
    assert "--panel-bed" in caplog.text
    assert panel_bed in caplog.text


def test_error_two_normal(
    balsamic_context: CGConfig, cli_runner: CliRunner, caplog: LogCaptureFixture
):
    """Test with case_id containing ONE tumor and TWO normal samples."""
    caplog.set_level(logging.ERROR)
    case_id = "balsamic_case_wgs_paired_two_normal_error"
    # WHEN dry running
    result = cli_runner.invoke(config_case, [case_id, "--dry-run"], obj=balsamic_context)
    # THEN command is NOT generated successfully
    assert result.exit_code != EXIT_SUCCESS
    # THEN log warning should be printed
    assert f"Case {case_id} has an invalid number of samples" in caplog.text


def test_error_wes_panel(
    balsamic_context: CGConfig, cli_runner: CliRunner, caplog: LogCaptureFixture
):
    """Test with case_id containing ONE tumor and TWO normal samples."""
    caplog.set_level(logging.ERROR)
    case_id = "balsamic_case_wes_panel_error"
    # WHEN dry running
    result = cli_runner.invoke(config_case, [case_id, "--dry-run"], obj=balsamic_context)
    # THEN command is NOT generated successfully
    assert result.exit_code != EXIT_SUCCESS
    # THEN log warning should be printed
    assert "requires a bed file" in caplog.text
