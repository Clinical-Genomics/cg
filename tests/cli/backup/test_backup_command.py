import logging
from pathlib import Path

from click.testing import CliRunner
from psutil import Process

from cg.cli.backup import backup_flow_cells, encrypt_flow_cells, fetch_flow_cell
from cg.constants import EXIT_SUCCESS, FileExtensions, FlowCellStatus
from cg.models.cg_config import CGConfig
from cg.models.run_devices.illumina_run_directory_data import IlluminaRunDirectoryData
from tests.store_helpers import StoreHelpers


def test_backup_flow_cells(
    cli_runner: CliRunner,
    cg_context: CGConfig,
    caplog,
    flow_cell_name: str,
    flow_cell_full_name: str,
    helpers: StoreHelpers,
):
    """Test backing up flow cell in dry run mode."""
    caplog.set_level(logging.DEBUG)

    # GIVEN a flow cells directory

    # Given a flow cell with no back-up
    helpers.add_flow_cell(
        store=cg_context.status_db, flow_cell_name=flow_cell_name, has_backup=False
    )

    # GIVEN an encrypted flow cell
    flow_cells_encrypt_dir = Path(cg_context.encryption.encryption_dir, flow_cell_full_name)
    flow_cells_encrypt_dir.mkdir(parents=True, exist_ok=True)
    Path(flow_cells_encrypt_dir, flow_cell_name).with_suffix(FileExtensions.COMPLETE).touch()

    # WHEN backing up flow cells in dry run mode
    result = cli_runner.invoke(backup_flow_cells, ["--dry-run"], obj=cg_context)

    # THEN exits without any errors
    assert result.exit_code == EXIT_SUCCESS


def test_backup_flow_cells_when_dsmc_is_running(
    cli_runner: CliRunner,
    cg_context: CGConfig,
    caplog,
    flow_cell_name: str,
    flow_cell_full_name: str,
    mocker,
):
    """Test backing-up flow cell in dry run mode when Dsmc processing has started."""
    caplog.set_level(logging.ERROR)

    # GIVEN a flow cells directory

    # GIVEN an ongoing Dsmc process
    mocker.patch.object(Process, "name", return_value="dsmc")

    # WHEN backing up flow cells in dry run mode
    result = cli_runner.invoke(backup_flow_cells, ["--dry-run"], obj=cg_context)

    # THEN exits without any errors
    assert result.exit_code == EXIT_SUCCESS

    # THEN communicate too many Dsmc processes are already running
    assert "Too many Dsmc processes are already running" in caplog.text


def test_backup_flow_cells_when_flow_cell_already_has_backup(
    cli_runner: CliRunner,
    cg_context: CGConfig,
    caplog,
    flow_cell_name: str,
    flow_cell_full_name: str,
    helpers: StoreHelpers,
):
    """Test backing-up flow cell in dry run mode when already backed-up."""
    caplog.set_level(logging.DEBUG)

    # GIVEN a flow cells directory

    # GIVEN a flow cell with a back-up
    helpers.add_flow_cell(
        store=cg_context.status_db, flow_cell_name=flow_cell_name, has_backup=True
    )

    # WHEN backing up flow cells in dry run mode
    result = cli_runner.invoke(backup_flow_cells, ["--dry-run"], obj=cg_context)

    # THEN exits without any errors
    assert result.exit_code == EXIT_SUCCESS

    # THEN communicate flow cell has already benn backed upped
    assert f"Flow cell: {flow_cell_name} is already backed-up" in caplog.text


def test_backup_flow_cells_when_encryption_is_not_completed(
    cli_runner: CliRunner,
    cg_context: CGConfig,
    caplog,
    flow_cell_name: str,
    flow_cell_full_name: str,
):
    """Test backing-up flow cell in dry run mode when encryption is not complete."""
    caplog.set_level(logging.DEBUG)

    # GIVEN a flow cells directory

    # WHEN backing up flow cells in dry run mode
    result = cli_runner.invoke(backup_flow_cells, ["--dry-run"], obj=cg_context)

    # THEN exits without any errors
    assert result.exit_code == EXIT_SUCCESS

    # THEN communicate flow cell encryption is not completed
    assert f"Flow cell: {flow_cell_name} encryption process is not complete" in caplog.text


def test_encrypt_flow_cells(
    cli_runner: CliRunner, cg_context: CGConfig, caplog, sbatch_job_number: str
):
    """Test encrypt flow cell in dry run mode."""
    caplog.set_level(logging.INFO)

    # GIVEN a flow cells directory

    # WHEN encrypting flow cells in dry run mode
    result = cli_runner.invoke(encrypt_flow_cells, ["--dry-run"], obj=cg_context)

    # THEN exits without any errors
    assert result.exit_code == EXIT_SUCCESS

    # THEN communicate flow cell encryption is submitted
    assert f"Flow cell encryption running as job {sbatch_job_number}" in caplog.text


def test_encrypt_flow_cells_when_already_backed_up(
    cli_runner: CliRunner,
    cg_context: CGConfig,
    caplog,
    flow_cell_name: str,
    helpers: StoreHelpers,
):
    """Test encrypt flow cell in dry run mode when there is already a back-up."""
    caplog.set_level(logging.DEBUG)

    # Given a flow cell with a back-up
    helpers.add_flow_cell(
        store=cg_context.status_db, flow_cell_name=flow_cell_name, has_backup=True
    )

    # GIVEN a flow cells directory

    # WHEN encrypting flow cells in dry run mode
    result = cli_runner.invoke(encrypt_flow_cells, ["--dry-run"], obj=cg_context)

    # THEN exits without any errors
    assert result.exit_code == EXIT_SUCCESS

    # THEN communicate flow cell is already backed-up
    assert f"Flow cell: {flow_cell_name} is already backed-up" in caplog.text


def test_encrypt_flow_cells_when_sequencing_not_done(
    cli_runner: CliRunner,
    cg_context: CGConfig,
    caplog,
    mocker,
    flow_cell_name: str,
):
    """Test encrypt flow cell in dry run mode when sequencing is not done."""
    caplog.set_level(logging.DEBUG)

    # GIVEN flow cells that are being sequenced
    mocker.patch.object(IlluminaRunDirectoryData, "is_sequencing_run_ready")
    IlluminaRunDirectoryData.is_sequencing_run_ready.return_value = False

    # GIVEN a flow cells directory

    # WHEN encrypting flow cells in dry run mode
    result = cli_runner.invoke(encrypt_flow_cells, ["--dry-run"], obj=cg_context)

    # THEN exits without any errors
    assert result.exit_code == EXIT_SUCCESS

    # THEN communicate flow cell is not ready
    assert f"Flow cell: {flow_cell_name} is not ready" in caplog.text


def test_encrypt_flow_cell_when_encryption_already_started(
    cli_runner: CliRunner,
    cg_context: CGConfig,
    caplog,
    pdc_archiving_dir: Path,
    flow_cell_name: str,
    flow_cell_full_name: str,
    mocker,
):
    """Test encrypt flow cell in dry run mode when pending file exists"""
    caplog.set_level(logging.DEBUG)

    # GIVEN flow cells that are ready
    mocker.patch.object(IlluminaRunDirectoryData, "is_sequencing_run_ready")
    IlluminaRunDirectoryData.is_sequencing_run_ready.return_value = True

    # GIVEN a pending flag file
    flow_cells_encrypt_dir = Path(cg_context.encryption.encryption_dir, flow_cell_full_name)
    flow_cells_encrypt_dir.mkdir(parents=True, exist_ok=True)
    Path(flow_cells_encrypt_dir, flow_cell_name).with_suffix(FileExtensions.PENDING).touch()

    # GIVEN a flow cells directory

    # WHEN encrypting flow cells in dry run mode
    result = cli_runner.invoke(encrypt_flow_cells, ["--dry-run"], obj=cg_context)

    # THEN exits without any errors
    assert result.exit_code == EXIT_SUCCESS

    # THEN communicate flow cell encryption already started
    assert f"Encryption already started for flow cell: {flow_cell_name}" in caplog.text


def test_encrypt_flow_cell_when_encryption_already_completed(
    cli_runner: CliRunner,
    cg_context: CGConfig,
    caplog,
    pdc_archiving_dir: Path,
    flow_cell_name: str,
    flow_cell_full_name: str,
    mocker,
):
    """Test encrypt flow cell in dry run mode when completed file exists"""
    caplog.set_level(logging.DEBUG)

    # GIVEN flow cells that are ready
    mocker.patch.object(IlluminaRunDirectoryData, "is_sequencing_run_ready")
    IlluminaRunDirectoryData.is_sequencing_run_ready.return_value = True

    # GIVEN a complete flag file
    flow_cells_encrypt_dir = Path(cg_context.encryption.encryption_dir, flow_cell_full_name)
    flow_cells_encrypt_dir.mkdir(parents=True, exist_ok=True)
    Path(flow_cells_encrypt_dir, flow_cell_name).with_suffix(FileExtensions.COMPLETE).touch()

    # GIVEN a flow cells directory

    # WHEN encrypting flow cells in dry run mode
    result = cli_runner.invoke(encrypt_flow_cells, ["--dry-run"], obj=cg_context)

    # THEN exits without any errors
    assert result.exit_code == EXIT_SUCCESS

    # THEN communicate flow cell encryption already completed
    assert f"Encryption already completed for flow cell: {flow_cell_name}" in caplog.text


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
    )

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
    )

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
    # GIVEN a non-existing flow cell id
    flow_cell_id = "hello"
    assert backup_context.status_db.get_flow_cell_by_name(flow_cell_id) is None

    # WHEN running the command with the non-existing flow cell id
    result = cli_runner.invoke(
        fetch_flow_cell, ["--flow-cell-id", flow_cell_id], obj=backup_context
    )

    # THEN assert that it exits with a non-zero exit code
    assert result.exit_code != 0
    # THEN assert that it was communicated that the flow cell does not exist
    assert f"{flow_cell_id}: not found" in caplog.text
