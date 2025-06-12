"""Test for the clean illumina runs cmd."""

import logging
from pathlib import Path
from unittest import mock

from click.testing import CliRunner

from cg.cli.clean import clean_illumina_runs
from cg.models.cg_config import CGConfig
from cg.models.run_devices.illumina_run_directory_data import IlluminaRunDirectoryData


def test_clean_illumina_runs_cmd(
    cli_runner: CliRunner,
    clean_illumina_sequencing_runs_context: CGConfig,
    tmp_sequencing_run_to_clean: IlluminaRunDirectoryData,
    tmp_sequencing_run_to_clean_path: Path,
    tmp_sequencing_run_not_to_clean_path: Path,
    tmp_sample_sheet_clean_illumina_sequencing_run_path: Path,
    caplog,
):
    """Test the clean flow cells command."""
    # GIVEN a config with StatusDB and Housekeeper
    caplog.set_level(logging.DEBUG)
    # GIVEN one sequencing run that should be cleaned and one that should not
    assert tmp_sequencing_run_not_to_clean_path.exists()
    assert tmp_sequencing_run_to_clean_path.exists()
    assert tmp_sample_sheet_clean_illumina_sequencing_run_path.exists()
    assert clean_illumina_sequencing_runs_context.status_db.get_illumina_sequencing_run_by_device_internal_id(
        tmp_sequencing_run_to_clean.id
    )
    assert clean_illumina_sequencing_runs_context.housekeeper_api.get_latest_bundle_version(
        "HLYWYDSXX"
    )
    # WHEN running the clean flow cells cli command
    with mock.patch(
        "cg.services.illumina.cleaning.clean_runs_service.IlluminaCleanRunsService.is_directory_older_than_21_days",
        return_value=True,
    ):
        result = cli_runner.invoke(clean_illumina_runs, obj=clean_illumina_sequencing_runs_context)

    # THEN assert it exits with success
    assert result.exit_code == 0

    # THEN the flow cell fulfilling all cleaning criteria is deleted
    assert not tmp_sequencing_run_to_clean_path.exists()
    assert "Successfully removed the directory and its contents" in caplog.text

    # THEN the flow cell not fulfilling all cleaning criteria is not deleted
    assert tmp_sequencing_run_not_to_clean_path.exists()
    assert "IlluminaCleanRunError" in caplog.text


def test_clean_illumina_runs_cmd_dry_run(
    cli_runner: CliRunner,
    clean_illumina_sequencing_runs_context: CGConfig,
    tmp_sequencing_run_to_clean_path: Path,
    tmp_sequencing_run_not_to_clean_path: Path,
    caplog,
):
    """Test the clean flow cells command using dry-run."""
    # GIVEN a config with StatusDB and Housekeeper
    caplog.set_level(logging.DEBUG)
    # GIVEN one flow cell that should be cleaned and one that should not
    assert tmp_sequencing_run_not_to_clean_path.exists()
    assert tmp_sequencing_run_to_clean_path.exists()
    # WHEN running the clean flow cells cli command
    with mock.patch(
        "cg.services.illumina.cleaning.clean_runs_service.IlluminaCleanRunsService.is_directory_older_than_21_days",
        return_value=True,
    ):
        result = cli_runner.invoke(
            clean_illumina_runs,
            ["--dry-run"],
            obj=clean_illumina_sequencing_runs_context,
        )

    # THEN assert it exits with success
    assert result.exit_code == 0

    # THEN the directory to clean is not deleted
    assert tmp_sequencing_run_to_clean_path.exists()
    assert tmp_sequencing_run_not_to_clean_path.exists()
    assert "Would have removed" in caplog.text
