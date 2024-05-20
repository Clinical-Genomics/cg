"""Test for the clean flow cells cmd."""

import logging
from pathlib import Path
from unittest import mock

from click.testing import CliRunner

from cg.cli.clean import clean_flow_cells
from cg.models.cg_config import CGConfig


def test_clean_flow_cells_cmd(
    cli_runner: CliRunner,
    clean_flow_cells_context: CGConfig,
    tmp_flow_cell_to_clean_path: Path,
    tmp_flow_cell_not_to_clean_path: Path,
    caplog,
):
    """Test the clean flow cells command."""
    # GIVEN a config with StatusDB and Housekeeper
    caplog.set_level(logging.DEBUG)
    # GIVEN one flow cell that should be cleaned and one that should not
    assert tmp_flow_cell_not_to_clean_path.exists()
    assert tmp_flow_cell_to_clean_path.exists()

    # WHEN running the clean flow cells cli command
    with mock.patch(
        "cg.meta.clean.clean_flow_cells.CleanFlowCellAPI.is_directory_older_than_21_days",
        return_value=True,
    ):
        result = cli_runner.invoke(clean_flow_cells, obj=clean_flow_cells_context)

    # THEN assert it exits with success
    assert result.exit_code == 0

    # THEN the flow cell fulfilling all cleaning criteria is deleted
    assert not tmp_flow_cell_to_clean_path.exists()
    assert "Successfully removed the directory and its contents" in caplog.text

    # THEN the flow cell not fulfilling all cleaning criteria is not deleted
    assert tmp_flow_cell_not_to_clean_path.exists()
    assert "CleanFlowCellFailedError" in caplog.text


def test_clean_flow_cells_cmd_dry_run(
    cli_runner: CliRunner,
    clean_flow_cells_context: CGConfig,
    tmp_flow_cell_to_clean_path: Path,
    tmp_flow_cell_not_to_clean_path: Path,
    caplog,
):
    """Test the clean flow cells command using dry-run."""
    # GIVEN a config with StatusDB and Housekeeper
    caplog.set_level(logging.DEBUG)
    # GIVEN one flow cell that should be cleaned and one that should not
    assert tmp_flow_cell_not_to_clean_path.exists()
    assert tmp_flow_cell_to_clean_path.exists()

    # WHEN running the clean flow cells cli command
    with mock.patch(
        "cg.meta.clean.clean_flow_cells.CleanFlowCellAPI.is_directory_older_than_21_days",
        return_value=True,
    ):
        result = cli_runner.invoke(clean_flow_cells, ["--dry-run"], obj=clean_flow_cells_context)

    # THEN assert it exits with success
    assert result.exit_code == 0

    # THEN the directory to clean is not deleted
    assert tmp_flow_cell_to_clean_path.exists()
    assert tmp_flow_cell_not_to_clean_path.exists()
    assert "Would have removed" in caplog.text
