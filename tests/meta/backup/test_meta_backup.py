"""Tests for the meta BackupAPI."""

from pathlib import Path

from cg.constants.demultiplexing import DemultiplexingDirsAndFiles
from cg.models.run_devices.illumina_run_directory_data import IlluminaRunDirectoryData
from cg.services.illumina.backup.backup_service import IlluminaBackupService


def test_create_copy_complete_file_exist(
    backup_api: IlluminaBackupService,
    novaseq_x_flow_cell: IlluminaRunDirectoryData,
):
    """Tests creating a copy complete file in the flow cell directory. There are two cases: when
    the file exists and when it does not exist."""

    # GIVEN a flow cell that has been decrypted in run_devices directory
    flow_cell_dir: Path = novaseq_x_flow_cell.path

    # GIVEN the copy complete to be created
    copy_complete_txt: str = DemultiplexingDirsAndFiles.COPY_COMPLETE

    # GIVEN a copy complete file exists
    flow_cell_dir.joinpath(copy_complete_txt).touch()

    # WHEN creating a copy complete file
    backup_api.create_copy_complete(flow_cell_dir)

    # THEN the copy complete file should exist in the flow cell directory
    assert flow_cell_dir.joinpath(copy_complete_txt).exists() is True


def test_create_copy_complete_file_does_not_exist(
    backup_api: IlluminaBackupService,
    novaseq_x_flow_cell: IlluminaRunDirectoryData,
):
    """Tests creating a copy complete file in the flow cell directory. There are two cases: when
    the file exists and when it does not exist."""

    # GIVEN a flow cell that has been decrypted in run_devices directory
    flow_cell_dir: Path = novaseq_x_flow_cell.path

    # GIVEN the copy complete to be created
    copy_complete_txt: str = DemultiplexingDirsAndFiles.COPY_COMPLETE

    # GIVEN that the copy complete file does not exists
    flow_cell_dir.joinpath(copy_complete_txt).unlink(missing_ok=True)

    # WHEN creating a copy complete file
    backup_api.create_copy_complete(flow_cell_dir)

    # THEN the copy complete file should exist in the flow cell directory
    assert flow_cell_dir.joinpath(copy_complete_txt).exists() is True
    assert flow_cell_dir.joinpath(copy_complete_txt).exists() is True
    assert flow_cell_dir.joinpath(copy_complete_txt).exists() is True
