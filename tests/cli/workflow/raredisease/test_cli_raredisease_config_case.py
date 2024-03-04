"""Tests cli methods to create the case config for Raredisease."""

import logging

from _pytest.logging import LogCaptureFixture
from click.testing import CliRunner

from cg.cli.workflow.raredisease.base import config_case
from cg.constants import EXIT_SUCCESS
from cg.models.cg_config import CGConfig


def test_config_case_dry_run(
    cli_runner: CliRunner,
    raredisease_context: CGConfig,
    caplog: LogCaptureFixture,
    raredisease_case_id: str,
):
    """Test dry-run."""
    caplog.set_level(logging.DEBUG)

    # GIVEN a valid case

    # WHEN performing a dry-run
    result = cli_runner.invoke(config_case, [raredisease_case_id, "-d"], obj=raredisease_context)

    # THEN command should should exit successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN sample sheet and parameters information should be collected
    assert "Getting sample sheet information" in caplog.text
    assert "Getting parameters information" in caplog.text

    # THEN sample sheet and parameters information files should not be written

    assert "Dry run: nextflow sample sheet and parameter file will not be written" in caplog.text
    assert "Writing sample sheet" not in caplog.text
    assert "Writing parameters file" not in caplog.text


def test_config_case_without_samples(
    cli_runner: CliRunner,
    raredisease_context: CGConfig,
    caplog: LogCaptureFixture,
    no_sample_case_id: str,
):
    """Test config_case with a case without samples."""
    caplog.set_level(logging.ERROR)
    # GIVEN a case

    # WHEN running config case
    result = cli_runner.invoke(config_case, [no_sample_case_id], obj=raredisease_context)

    # THEN command should not exit successfully
    assert result.exit_code != EXIT_SUCCESS

    # THEN warning should be printed that no sample is found
    assert no_sample_case_id in caplog.text
    assert "has no samples" in caplog.text


def test_config_case(
    cli_runner: CliRunner,
    raredisease_context: CGConfig,
    # rnafusion_sample_sheet_path: Path,
    # rnafusion_params_file_path: Path,
    caplog: LogCaptureFixture,
    raredisease_case_id: str,
):
    """Test case-config."""
    caplog.set_level(logging.DEBUG)

    # GIVEN a valid case

    # WHEN performing a dry-run
    result = cli_runner.invoke(config_case, [raredisease_case_id], obj=raredisease_context)

    # THEN command should should exit successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN sample sheet and parameters information should be collected
    assert "Getting sample sheet information" in caplog.text
    assert "Getting parameters information" in caplog.text

    # THEN sample sheet and parameters information files should be written

    assert (
        "Dry run: nextflow sample sheet and parameter file will not be written" not in caplog.text
    )
    assert "Could not create config files" not in caplog.text
    assert "Writing sample sheet" in caplog.text
    assert "Writing parameters file" in caplog.text
