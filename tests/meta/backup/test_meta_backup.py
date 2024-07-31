"""Tests for the meta BackupAPI."""

import logging
import subprocess
from pathlib import Path
import mock
from mock import call
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import FileExtensions
from cg.constants.demultiplexing import DemultiplexingDirsAndFiles
from cg.exc import ChecksumFailedError
from cg.meta.backup.backup import SpringBackupAPI
from cg.services.illumina.backup.backup_service import IlluminaBackupService
from cg.services.pdc_service.pdc_service import PdcService
from cg.meta.encryption.encryption import SpringEncryptionAPI
from cg.models.run_devices.illumina_run_directory_data import IlluminaRunDirectoryData
from tests.mocks.hk_mock import MockFile


@mock.patch("cg.meta.backup.backup.SpringBackupAPI.is_spring_file_archived")
@mock.patch("cg.meta.backup.backup.SpringBackupAPI.remove_archived_spring_file")
@mock.patch("cg.meta.backup.backup.SpringBackupAPI.mark_file_as_archived")
@mock.patch("cg.apps.housekeeper.hk.HousekeeperAPI")
@mock.patch("cg.meta.encryption.encryption.SpringEncryptionAPI")
@mock.patch("cg.services.pdc_service.pdc_service.PdcService")
def test_encrypt_and_archive_spring_file(
    mock_pdc_service: PdcService,
    mock_spring_encryption_api: SpringEncryptionAPI,
    mock_housekeeper: HousekeeperAPI,
    mock_mark_file_as_archived,
    mock_remove_archived_spring_files,
    mock_is_archived,
    spring_file_path,
):
    # GIVEN a spring file that needs to be encrypted and archived to PDC and that is not already
    # archived
    spring_backup_api = SpringBackupAPI(
        encryption_api=mock_spring_encryption_api,
        hk_api=mock_housekeeper,
        pdc_service=mock_pdc_service,
    )
    mock_is_archived.return_value = False

    # WHEN running the encryption and archiving process
    mock_spring_encryption_api.encrypted_spring_file_path.return_value = (
        spring_file_path.with_suffix(FileExtensions.SPRING + FileExtensions.GPG)
    )
    mock_spring_encryption_api.encrypted_key_path.return_value = spring_file_path.with_suffix(
        FileExtensions.KEY + FileExtensions.GPG
    )
    spring_backup_api.encrypt_and_archive_spring_file(spring_file_path)

    # THEN the spring file directory should be cleaned up first
    mock_spring_encryption_api.cleanup.assert_called_with(spring_file_path)

    # AND the spring file should be encrypted
    mock_spring_encryption_api.spring_symmetric_encryption.assert_called_once_with(spring_file_path)

    # AND the key should be encrypted
    mock_spring_encryption_api.key_asymmetric_encryption.assert_called_once_with(spring_file_path)

    # AND the encryption result should be checked
    mock_spring_encryption_api.compare_spring_file_checksums.assert_called_once_with(
        spring_file_path
    )

    # AND the encrypted spring file AND the encrypted key should be archived
    calls = [
        call(
            file_path=str(mock_spring_encryption_api.encrypted_spring_file_path.return_value),
        ),
        call(
            file_path=str(mock_spring_encryption_api.encrypted_key_path.return_value),
        ),
    ]
    mock_pdc_service.archive_file_to_pdc.assert_has_calls(calls)

    # AND the spring file should be marked as archived in Housekeeper
    mock_mark_file_as_archived.assert_called_once_with(spring_file_path)

    # AND the original spring file should be removed
    mock_remove_archived_spring_files.assert_called_once_with(spring_file_path)


@mock.patch("cg.meta.backup.backup.SpringBackupAPI.is_spring_file_archived")
@mock.patch("cg.apps.housekeeper.hk")
@mock.patch("cg.meta.encryption.encryption")
@mock.patch("cg.services.pdc_service.pdc_service.PdcService")
def test_encrypt_and_archive_spring_file_checksum_failed(
    mock_pdc_service: PdcService,
    mock_spring_encryption_api: SpringEncryptionAPI,
    mock_housekeeper: HousekeeperAPI,
    mock_is_archived,
    spring_file_path,
    caplog,
):
    # GIVEN a spring file that needs to be encrypted and archived to PDC
    spring_backup_api = SpringBackupAPI(
        encryption_api=mock_spring_encryption_api,
        hk_api=mock_housekeeper,
        pdc_service=mock_pdc_service,
    )

    # WHEN running the encryption and archiving process
    mock_is_archived.return_value = False
    mock_spring_encryption_api.encrypted_spring_file_path.return_value = (
        spring_file_path.with_suffix(FileExtensions.SPRING + FileExtensions.GPG)
    )
    mock_spring_encryption_api.encrypted_key_path.return_value = spring_file_path.with_suffix(
        FileExtensions.KEY + FileExtensions.GPG
    )

    mock_spring_encryption_api.compare_spring_file_checksums.side_effect = ChecksumFailedError(
        "Checksum comparison failed!"
    )

    spring_backup_api.encrypt_and_archive_spring_file(spring_file_path)

    # THEN the checksum failure should be logged
    assert "Checksum comparison failed!" in caplog.text


@mock.patch("cg.apps.housekeeper.hk")
@mock.patch("cg.meta.encryption.encryption")
@mock.patch("cg.services.pdc_service.pdc_service.PdcService")
def test_mark_file_as_archived(
    mock_pdc_service: PdcService,
    mock_spring_encryption_api: SpringEncryptionAPI,
    mock_housekeeper: HousekeeperAPI,
    spring_file_path,
    caplog,
):
    caplog.set_level(logging.INFO)
    # GIVEN a file
    spring_backup_api = SpringBackupAPI(
        encryption_api=mock_spring_encryption_api,
        hk_api=mock_housekeeper,
        pdc_service=mock_pdc_service,
    )
    mock_housekeeper_file = MockFile(id=0, path=spring_file_path, to_archive=False)
    mock_housekeeper.files.return_value.first.return_value = mock_housekeeper_file

    # WHEN marking the file as archived
    spring_backup_api.mark_file_as_archived(spring_file_path)

    # THEN the set_to_archive method in the Housekeeper API should be called with the new value True
    mock_housekeeper.set_to_archive.assert_called_once_with(file=mock_housekeeper_file, value=True)
    assert f"Setting {spring_file_path} to archived in Housekeeper" in caplog.text


@mock.patch("cg.apps.housekeeper.hk")
@mock.patch("cg.meta.encryption.encryption")
@mock.patch("cg.services.pdc_service.pdc_service.PdcService")
def test_mark_file_as_archived_dry_run(
    mock_pdc_service: PdcService,
    mock_spring_encryption_api: SpringEncryptionAPI,
    mock_housekeeper: HousekeeperAPI,
    caplog,
    spring_file_path,
):
    caplog.set_level(logging.INFO)
    # GIVEN a file and running as a dry run
    spring_backup_api = SpringBackupAPI(
        encryption_api=mock_spring_encryption_api,
        hk_api=mock_housekeeper,
        pdc_service=mock_pdc_service,
        dry_run=True,
    )
    mock_housekeeper_file = MockFile(id=0, path=spring_file_path, to_archive=False)
    mock_housekeeper.files.return_value.first.return_value = mock_housekeeper_file

    # WHEN marking the file as archived
    spring_backup_api.mark_file_as_archived(spring_file_path)

    # THEN the set_to_archive method in the Housekeeper API should be called with the new value True
    mock_housekeeper.set_to_archive.assert_not_called()
    assert f"Dry run, no changes made to {spring_file_path}" in caplog.text


@mock.patch("cg.apps.housekeeper.hk")
@mock.patch("cg.meta.encryption.encryption")
@mock.patch("cg.services.pdc_service.pdc_service.PdcService")
def test_decrypt_and_retrieve_spring_file(
    mock_pdc_service: PdcService,
    mock_spring_encryption_api: SpringEncryptionAPI,
    mock_housekeeper: HousekeeperAPI,
    spring_file_path,
):
    # GIVEN a spring file that needs to be decrypted and retrieved from PDC
    spring_backup_api = SpringBackupAPI(
        encryption_api=mock_spring_encryption_api,
        hk_api=mock_housekeeper,
        pdc_service=mock_pdc_service,
    )

    # WHEN running the decryption and retrieval process
    mock_spring_encryption_api.encrypted_spring_file_path.return_value = (
        spring_file_path.with_suffix(FileExtensions.SPRING + FileExtensions.GPG)
    )
    mock_spring_encryption_api.encrypted_key_path.return_value = spring_file_path.with_suffix(
        FileExtensions.KEY + FileExtensions.GPG
    )
    spring_backup_api.retrieve_and_decrypt_spring_file(spring_file_path)

    # THEN the encrypted spring file AND the encrypted key should be retrieved
    calls = [
        call(file_path=str(mock_spring_encryption_api.encrypted_spring_file_path.return_value)),
        call(file_path=str(mock_spring_encryption_api.encrypted_key_path.return_value)),
    ]
    mock_pdc_service.retrieve_file_from_pdc.assert_has_calls(calls)


@mock.patch("cg.apps.housekeeper.hk")
@mock.patch("cg.meta.encryption.encryption")
@mock.patch("cg.services.pdc_service.pdc_service.PdcService")
def test_decrypt_and_retrieve_spring_file_pdc_retrieval_failed(
    mock_pdc: PdcService,
    mock_spring_encryption_api: SpringEncryptionAPI,
    mock_housekeeper: HousekeeperAPI,
    spring_file_path,
    caplog,
):
    # GIVEN a spring file that needs to be encrypted and archived to PDC
    spring_backup_api = SpringBackupAPI(
        encryption_api=mock_spring_encryption_api, hk_api=mock_housekeeper, pdc_service=mock_pdc
    )

    # WHEN running the encryption and archiving process
    mock_spring_encryption_api.encrypted_spring_file_path.return_value = (
        spring_file_path.with_suffix(FileExtensions.SPRING + FileExtensions.GPG)
    )
    mock_spring_encryption_api.encrypted_key_path.return_value = spring_file_path.with_suffix(
        FileExtensions.KEY + FileExtensions.GPG
    )
    mock_pdc.retrieve_file_from_pdc.side_effect = subprocess.CalledProcessError(1, "echo")
    spring_backup_api.retrieve_and_decrypt_spring_file(spring_file_path=spring_file_path)

    # THEN the decryption failure should be logged
    assert "Decryption failed" in caplog.text


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
