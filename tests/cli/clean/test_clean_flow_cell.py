"""Test for the clean flow cells cmd."""
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
):
    """Test the clean flow cells cmd"""
    # GIVEN a config with StatusDB and Housekeeper that contain a flow cell that can be cleaned

    # GIVEN that the flow cells exist
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

    # THEN the flow cell not fulfilling all cleaning criteria is not deleted
    assert tmp_flow_cell_not_to_clean_path.exists()


def test_clean_flow_cells_cmd_dry_run(
    cli_runner: CliRunner,
    clean_flow_cells_context: CGConfig,
    tmp_flow_cell_to_clean_path: Path,
    tmp_flow_cell_not_to_clean_path: Path,
):
    """Test the clean flow cells cmd"""
    # GIVEN a config with StatusDB and Housekeeper that contain a flow cell that can be cleaned

    # GIVEN that the flow cells exist
    assert tmp_flow_cell_not_to_clean_path.exists()
    assert tmp_flow_cell_to_clean_path.exists()

    # WHEN running the clean flow cells cli command
    with mock.patch(
        "cg.meta.clean.clean_flow_cells.CleanFlowCellAPI.is_directory_older_than_21_days",
        return_value=True,
    ):
        result = cli_runner.invoke(clean_flow_cells, ["-d"], obj=clean_flow_cells_context)

    # THEN assert it exits with success
    assert result.exit_code == 0

    # THEN the directory to clean is not deleted
    assert tmp_flow_cell_to_clean_path.exists()
