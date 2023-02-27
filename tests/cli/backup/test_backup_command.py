import logging

from click.testing import CliRunner

from cg.cli.backup import fetch_flow_cell
from cg.constants import FlowCellStatus, EXIT_SUCCESS
from cg.models.cg_config import CGConfig


def test_run_fetch_flow_cell_dry_run_no_flow_cell_specified(
    cli_runner: CliRunner, backup_context: CGConfig, caplog
):
    """Test fetching flow cell when no flow cells with correct status."""
    caplog.set_level(logging.INFO)

    # GIVEN a context with a backup_api
    assert "backup_api" in backup_context.meta_apis

    # GIVEN that there are no flow cells set to "requested" in status_db
    assert not backup_context.status_db.get_flow_cells_by_statuses(
        flow_cell_statuses=[FlowCellStatus.REQUESTED]
    ).first()

    # WHEN running the fetch flow cell command without specifying any flow cell in dry run mode
    result = cli_runner.invoke(fetch_flow_cell, ["--dry-run"], obj=backup_context)

    # THEN assert that it exits without any problems
    assert result.exit_code == EXIT_SUCCESS

    # THEN assert that it is communicated that no flow cells are requested
    assert "No flow cells requested" in caplog.text


def test_run_fetch_flow_cell_dry_run_retrieval_time(
    cli_runner: CliRunner, backup_context: CGConfig, caplog, mocker
):
    """Test fetching flow cell retrieval time."""
    caplog.set_level(logging.INFO)

    # GIVEN a context with a backup_api
    assert "backup_api" in backup_context.meta_apis

    # GIVEN that there are no flow cells set to "requested" in status_db
    assert not backup_context.status_db.get_flow_cells_by_statuses(
        flow_cell_statuses=[FlowCellStatus.REQUESTED]
    ).first()

    # GIVEN that the backup api returns a retrieval time
    expected_time = 60
    mocker.patch("cg.meta.backup.backup.BackupAPI.fetch_flow_cell", return_value=expected_time)

    # WHEN running the fetch flow cell command without specifying any flow cell in dry run mode
    result = cli_runner.invoke(fetch_flow_cell, ["--dry-run"], obj=backup_context)

    # THEN assert that it exits without any problems
    assert result.exit_code == EXIT_SUCCESS

    # THEN assert that it is communicated that a retrieval time was found
    assert "Retrieval time" in caplog.text


def test_run_fetch_flow_cell_non_existing_flow_cell(
    cli_runner: CliRunner, backup_context: CGConfig, caplog
):
    # GIVEN a context with a backup api
    # GIVEN a non existing flow cell id
    flow_cell_id = "hello"
    assert backup_context.status_db.get_flow_cell(flow_cell_id) is None

    # WHEN running the command with the non existing flow cell id
    result = cli_runner.invoke(
        fetch_flow_cell, ["--flow-cell-id", flow_cell_id], obj=backup_context
    )

    # THEN assert that it exits with a non zero exit code
    assert result.exit_code != 0
    # THEN assert that it was communicated that the flow cell does not exist
    assert f"{flow_cell_id}: not found" in caplog.text
