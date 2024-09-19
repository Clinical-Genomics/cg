import logging
from pathlib import Path

import pytest
from click.testing import CliRunner
from psutil import Process

from cg.cli.backup import backup_illumina_runs, encrypt_illumina_runs, fetch_illumina_run
from cg.constants import EXIT_SUCCESS, FileExtensions, SequencingRunDataAvailability
from cg.exc import IlluminaRunEncryptionError
from cg.models.cg_config import CGConfig
from cg.models.run_devices.illumina_run_directory_data import IlluminaRunDirectoryData
from cg.store.models import IlluminaSequencingRun
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


def test_backup_illumina_runs(
    cli_runner: CliRunner,
    backup_context: CGConfig,
    caplog,
    novaseq_x_flow_cell_id: str,
    novaseq_x_flow_cell_full_name: str,
    helpers: StoreHelpers,
):
    """Test backing up an Illumina run in dry run mode."""
    caplog.set_level(logging.DEBUG)

    # GIVEN a sequencing run without back-up
    sequencing_run: IlluminaSequencingRun = (
        backup_context.status_db.get_illumina_sequencing_run_by_device_internal_id(
            novaseq_x_flow_cell_id
        )
    )
    assert not sequencing_run.has_backup

    # GIVEN an encrypted run
    run_encrypt_dir = Path(backup_context.encryption.encryption_dir, novaseq_x_flow_cell_full_name)
    run_encrypt_dir.mkdir(parents=True, exist_ok=True)
    Path(run_encrypt_dir, novaseq_x_flow_cell_id).with_suffix(FileExtensions.COMPLETE).touch()

    # WHEN backing up runs in dry run mode
    result = cli_runner.invoke(backup_illumina_runs, ["--dry-run"], obj=backup_context)

    # THEN exits without any errors
    assert result.exit_code == EXIT_SUCCESS


def test_backup_illumina_runs_when_dsmc_is_running(
    cli_runner: CliRunner,
    context_with_illumina_data: CGConfig,
    caplog,
    mocker,
):
    """Test backing-up Illumina runs in dry run mode when Dsmc processing has started."""
    caplog.set_level(logging.ERROR)

    # GIVEN an ongoing Dsmc process
    mocker.patch.object(Process, "name", return_value="dsmc")

    # WHEN backing up Illumina runs in dry run mode
    result = cli_runner.invoke(backup_illumina_runs, ["--dry-run"], obj=context_with_illumina_data)

    # THEN exits without any errors
    assert result.exit_code == EXIT_SUCCESS

    # THEN communicate too many Dsmc processes are already running
    assert "Too many Dsmc processes are already running" in caplog.text


def test_backup_illumina_run_when_run_already_has_backup(
    cli_runner: CliRunner,
    context_with_illumina_data: CGConfig,
    caplog,
    store_with_illumina_sequencing_data: Store,
    novaseq_x_flow_cell_id: str,
    helpers: StoreHelpers,
):
    """Test backing-up an Illumina run in dry run mode when already backed-up."""
    caplog.set_level(logging.DEBUG)

    # GIVEN a store with a backed up sequencing run
    context_with_illumina_data.status_db_ = store_with_illumina_sequencing_data
    sequencing_run: IlluminaSequencingRun = (
        store_with_illumina_sequencing_data.get_illumina_sequencing_run_by_device_internal_id(
            novaseq_x_flow_cell_id
        )
    )
    sequencing_run.has_backup = True

    # WHEN backing up Illumina runs in dry run mode
    result = cli_runner.invoke(backup_illumina_runs, ["--dry-run"], obj=context_with_illumina_data)

    # THEN exits without any errors
    assert result.exit_code == EXIT_SUCCESS

    # THEN communicate the sequencing run has already benn backed upped
    assert (
        f"Sequencing run for flow cell: {novaseq_x_flow_cell_id} is already backed-up"
        in caplog.text
    )


def test_backup_illumina_runs_when_encryption_is_not_completed(
    cli_runner: CliRunner,
    context_with_illumina_data: CGConfig,
    caplog,
    novaseq_x_flow_cell_id: str,
):
    """Test backing-up Illumina run in dry run mode when encryption is not complete."""
    caplog.set_level(logging.DEBUG)

    # WHEN backing up Illumina runs in dry run mode
    result = cli_runner.invoke(backup_illumina_runs, ["--dry-run"], obj=context_with_illumina_data)

    # THEN exits without any errors
    assert result.exit_code == EXIT_SUCCESS

    # THEN communicate runs encryption is not completed
    assert (
        f"Sequencing run for flow cell: {novaseq_x_flow_cell_id} encryption process is not complete"
        in caplog.text
    )


def test_encrypt_illumina_runs(
    cli_runner: CliRunner, context_with_illumina_data: CGConfig, caplog, sbatch_job_number: str
):
    """Test encrypt Illumina runs in dry run mode."""
    caplog.set_level(logging.INFO)

    # WHEN encrypting run in dry run mode
    result = cli_runner.invoke(encrypt_illumina_runs, ["--dry-run"], obj=context_with_illumina_data)

    # THEN exits without any errors
    assert result.exit_code == EXIT_SUCCESS

    # THEN communicate encryption job is submitted
    assert f"Run encryption running as job {sbatch_job_number}" in caplog.text


def test_encrypt_illumina_runs_when_already_backed_up(
    cli_runner: CliRunner,
    context_with_illumina_data: CGConfig,
    caplog,
    novaseq_x_flow_cell_id: str,
    store_with_illumina_sequencing_data: Store,
    helpers: StoreHelpers,
):
    """Test encrypt Illumina run in dry run mode when there is already a back-up."""
    caplog.set_level(logging.DEBUG)

    # GIVEN a sequencing run with a back-up
    context_with_illumina_data.status_db_ = store_with_illumina_sequencing_data
    sequencing_run: IlluminaSequencingRun = (
        store_with_illumina_sequencing_data.get_illumina_sequencing_run_by_device_internal_id(
            novaseq_x_flow_cell_id
        )
    )
    sequencing_run.has_backup = True

    # GIVEN a sequencing runs directory

    # WHEN encrypting runs in dry run mode
    result = cli_runner.invoke(encrypt_illumina_runs, ["--dry-run"], obj=context_with_illumina_data)

    # THEN exits without any errors
    assert result.exit_code == EXIT_SUCCESS

    # THEN communicate run is already backed-up
    assert f"Run: {novaseq_x_flow_cell_id} is already backed-up" in caplog.text


def test_encrypt_illumina_run_when_sequencing_not_done(
    cli_runner: CliRunner,
    context_with_illumina_data: CGConfig,
    caplog,
    mocker,
    novaseq_x_flow_cell_id: str,
):
    """Test encrypt Illumina runs in dry run mode when sequencing is not done."""
    caplog.set_level(logging.DEBUG)

    # GIVEN Illumina runs that are being sequenced
    mocker.patch.object(IlluminaRunDirectoryData, "is_sequencing_run_ready")
    IlluminaRunDirectoryData.is_sequencing_run_ready.return_value = False

    # GIVEN a sequencing runs directory

    # WHEN encrypting runs in dry run mode
    result = cli_runner.invoke(encrypt_illumina_runs, ["--dry-run"], obj=context_with_illumina_data)

    # THEN exits without any errors
    assert result.exit_code == EXIT_SUCCESS

    # THEN communicate the run is not ready
    assert f"Run: {novaseq_x_flow_cell_id} is not ready" in caplog.text


def test_encrypt_illumina_run_when_encryption_already_started(
    cli_runner: CliRunner,
    encryption_context: CGConfig,
    caplog,
    pdc_archiving_dir: Path,
    novaseq_x_flow_cell_id: str,
    novaseq_x_flow_cell_full_name: str,
    store_with_illumina_sequencing_data: Store,
    tmp_path: Path,
    mocker,
):
    """Test encrypt Illumina runs in dry run mode when pending file exists"""
    caplog.set_level(logging.DEBUG)

    # GIVEN Illumina runs that are ready
    mocker.patch.object(IlluminaRunDirectoryData, "is_sequencing_run_ready")
    IlluminaRunDirectoryData.is_sequencing_run_ready.return_value = True

    # GIVEN a pending flag file
    Path(
        encryption_context.encryption.encryption_dir,
        novaseq_x_flow_cell_full_name,
        novaseq_x_flow_cell_id,
    ).with_suffix(FileExtensions.PENDING).touch()

    # WHEN encrypting Illumina runs in dry run mode
    result = cli_runner.invoke(encrypt_illumina_runs, ["--dry-run"], obj=encryption_context)

    # THEN exits without any errors
    assert result.exit_code == EXIT_SUCCESS

    # THEN communicate flow cell encryption already started
    assert f"Encryption already started for run: {novaseq_x_flow_cell_id}" in caplog.text


def test_encrypt_illumina_run_when_encryption_already_completed(
    cli_runner: CliRunner,
    encryption_context: CGConfig,
    novaseq_x_flow_cell_full_name: str,
    novaseq_x_flow_cell_id: str,
    caplog,
    pdc_archiving_dir: Path,
    mocker,
):
    """Test encrypt Illumina runs in dry run mode when completed file exists"""
    caplog.set_level(logging.DEBUG)

    # GIVEN Illumina runs that are ready
    mocker.patch.object(IlluminaRunDirectoryData, "is_sequencing_run_ready")
    IlluminaRunDirectoryData.is_sequencing_run_ready.return_value = True

    # GIVEN a complete flag file
    Path(
        encryption_context.encryption.encryption_dir,
        novaseq_x_flow_cell_full_name,
        novaseq_x_flow_cell_id,
    ).with_suffix(FileExtensions.COMPLETE).touch()

    # WHEN encrypting Illumina runs in dry run mode
    result = cli_runner.invoke(encrypt_illumina_runs, ["--dry-run"], obj=encryption_context)

    # THEN exits without any errors
    assert result.exit_code == EXIT_SUCCESS

    # THEN communicate flow cell encryption already completed
    assert f"Encryption already completed for run: {novaseq_x_flow_cell_id}" in caplog.text


def test_run_fetch_sequencing_run_dry_run_no_run_specified(
    cli_runner: CliRunner, backup_context: CGConfig, caplog
):
    """Test fetching flow cell when no Illumina runs with correct status."""
    caplog.set_level(logging.INFO)

    # GIVEN a context with a backup_api
    assert "backup_api" in backup_context.meta_apis

    # GIVEN that there are no Illumina runs set to "requested" in status_db
    assert not backup_context.status_db.get_illumina_sequencing_runs_by_data_availability(
        data_availability=[SequencingRunDataAvailability.REQUESTED]
    )

    # WHEN running the fetch_illumina_run command without specifying any flow cell in dry run mode
    result = cli_runner.invoke(fetch_illumina_run, ["--dry-run"], obj=backup_context)

    # THEN assert that it exits without any problems
    assert result.exit_code == EXIT_SUCCESS

    # THEN assert that it is communicated that no Illumina runs are requested
    assert "No sequencing run requested" in caplog.text


def test_run_fetch_sequencing_run_dry_run_retrieval_time(
    cli_runner: CliRunner, backup_context: CGConfig, caplog, mocker
):
    """Test fetching Illumina run retrieval time."""
    caplog.set_level(logging.INFO)

    # GIVEN a context with a backup_api
    assert "backup_api" in backup_context.meta_apis

    # GIVEN that there are no Illumina runs set to "requested" in status_db
    assert not backup_context.status_db.get_illumina_sequencing_runs_by_data_availability(
        data_availability=[SequencingRunDataAvailability.REQUESTED]
    )

    # GIVEN that the backup api returns a retrieval time
    expected_time = 60
    mocker.patch(
        "cg.services.illumina.backup.backup_service.IlluminaBackupService.fetch_sequencing_run",
        return_value=expected_time,
    )

    # WHEN running the fetch Illumina run command without specifying any illumina in dry run mode
    result = cli_runner.invoke(fetch_illumina_run, ["--dry-run"], obj=backup_context)

    # THEN assert that it exits without any problems
    assert result.exit_code == EXIT_SUCCESS

    # THEN assert that it is communicated that a retrieval time was found
    assert "Retrieval time" in caplog.text


def test_run_fetch_illumina_run_non_existing_flow_cell(
    cli_runner: CliRunner, backup_context: CGConfig, caplog
):
    # GIVEN a context with a backup api

    # GIVEN a non-existing flow cell id
    flow_cell_id = "non-existing-id"

    # WHEN running the command with the non-existing flow cell id
    result = cli_runner.invoke(
        fetch_illumina_run, ["--flow-cell-id", flow_cell_id], obj=backup_context
    )

    # THEN assert that it exits with a non-zero exit code
    assert result.exit_code != 0
