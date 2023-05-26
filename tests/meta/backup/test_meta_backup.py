"""Tests for the meta BackupAPI"""

import logging
import subprocess

import mock
import pytest
from mock import call

from cg.constants.sequencing import Sequencers
from tests.mocks.hk_mock import MockFile

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import FileExtensions, FlowCellStatus
from cg.exc import ChecksumFailedError
from cg.meta.backup.backup import BackupAPI, SpringBackupAPI
from cg.meta.backup.pdc import PdcAPI
from cg.meta.encryption.encryption import SpringEncryptionAPI


@mock.patch("cg.store.Store")
def test_maximum_processing_queue_full(mock_store):
    """Tests check_processing method of the backup API"""
    # GIVEN a flow cell needs to be retrieved from PDC
    backup_api = BackupAPI(
        encryption_api=mock.Mock(),
        encrypt_dir=mock.Mock(),
        status=mock_store,
        tar_api=mock.Mock(),
        pdc_api=mock.Mock(),
        root_dir=mock.Mock(),
    )

    # WHEN there's already a flow cell being retrieved from PDC
    mock_store.get_flow_cells_by_statuses.return_value = [[mock.Mock()]]

    # THEN this method should return False
    assert backup_api.check_processing() is False


@mock.patch("cg.store")
def test_maximum_processing_queue_not_full(mock_store):
    """Tests check_processing method of the backup API"""
    # GIVEN a flow cell needs to be retrieved from PDC
    backup_api = BackupAPI(
        encryption_api=mock.Mock(),
        encrypt_dir=mock.Mock(),
        status=mock_store,
        tar_api=mock.Mock(),
        pdc_api=mock.Mock(),
        root_dir=mock.Mock(),
    )
    # WHEN there are no flow cells being retrieved from PDC
    mock_store.get_flow_cells_by_statuses().return_value = []

    # THEN this method should return True
    assert backup_api.check_processing() is True


@mock.patch("cg.store.models.Flowcell")
@mock.patch("cg.store")
def test_get_first_flow_cell_next_requested(mock_store, mock_flow_cell):
    """Tests get_first_flow_cell method of the backup API when requesting next flow cell"""
    # GIVEN status-db needs to be checked for flow cells to be retrieved from PDC
    backup_api = BackupAPI(
        encryption_api=mock.Mock(),
        encrypt_dir=mock.Mock(),
        status=mock_store,
        tar_api=mock.Mock(),
        pdc_api=mock.Mock(),
        root_dir=mock.Mock(),
    )

    # WHEN a flow cell is requested to be retrieved from PDC
    mock_store.get_flow_cells_by_statuses().return_value = [mock_flow_cell]

    popped_flow_cell = backup_api.get_first_flow_cell()

    # THEN a flow cell is returned
    assert popped_flow_cell is not None


@mock.patch("cg.store")
def test_get_first_flow_cell_no_flow_cell_requested(mock_store):
    """Tests get_first_flow_cell method of the backup API when no flow cell requested"""
    # GIVEN status-db needs to be checked for flow cells to be retrieved from PDC
    backup_api = BackupAPI(
        encryption_api=mock.Mock(),
        encrypt_dir=mock.Mock(),
        status=mock_store,
        tar_api=mock.Mock(),
        pdc_api=mock.Mock(),
        root_dir=mock.Mock(),
    )

    # WHEN there are no flow cells requested to be retrieved from PDC
    mock_store.get_flow_cells_by_statuses.return_value = []

    popped_flow_cell = backup_api.get_first_flow_cell()

    # THEN no flow cell is returned
    assert popped_flow_cell is None


@mock.patch("cg.meta.backup.backup.BackupAPI.check_processing")
@mock.patch("cg.store.models.Flowcell")
def test_fetch_flow_cell_processing_queue_full(mock_flow_cell, mock_check_processing, caplog):
    """Tests the fetch_flow_cell method of the backup API when processing queue is full"""

    caplog.set_level(logging.INFO)

    # GIVEN we check if a flow cell needs to be retrieved from PDC
    backup_api = BackupAPI(
        encryption_api=mock.Mock(),
        encrypt_dir=mock.Mock(),
        status=mock.Mock(),
        tar_api=mock.Mock(),
        pdc_api=mock.Mock(),
        root_dir=mock.Mock(),
    )

    # WHEN the processing queue is full
    backup_api.check_processing.return_value = False
    result = backup_api.fetch_flow_cell(mock_flow_cell)

    # THEN no flow cell will be fetched and a log message indicates that the processing queue is
    # full
    assert result is None
    assert "Processing queue is full" in caplog.text


@mock.patch("cg.meta.backup.backup.BackupAPI.get_first_flow_cell")
@mock.patch("cg.meta.backup.backup.BackupAPI.check_processing")
@mock.patch("cg.store")
def test_fetch_flow_cell_no_flow_cells_requested(
    mock_store,
    mock_check_processing,
    mock_get_first_flow_cell,
    caplog,
):
    """Tests the fetch_flow_cell method of the backup API when no flow cell requested"""

    caplog.set_level(logging.INFO)

    # GIVEN we check if a flow cell needs to be retrieved from PDC
    backup_api = BackupAPI(
        encryption_api=mock.Mock(),
        encrypt_dir=mock.Mock(),
        status=mock_store,
        tar_api=mock.Mock(),
        pdc_api=mock.Mock(),
        root_dir=mock.Mock(),
    )

    # WHEN no flow cells are requested
    backup_api.get_first_flow_cell.return_value = None
    backup_api.check_processing.return_value = True

    # AND no flow cell has been specified
    mock_flow_cell = None

    result = backup_api.fetch_flow_cell(mock_flow_cell)

    # THEN no flow cell will be fetched and a log message indicates that no flow cells have been
    # requested
    assert result is None
    assert "No flow cells requested" in caplog.text


@mock.patch("cg.meta.backup.backup.BackupAPI.unlink_files")
@mock.patch("cg.meta.backup.backup.BackupAPI.create_rta_complete")
@mock.patch("cg.meta.backup.backup.BackupAPI.get_archived_flow_cell_path")
@mock.patch("cg.meta.backup.backup.BackupAPI.get_archived_encryption_key_path")
@mock.patch("cg.meta.backup.backup.BackupAPI.check_processing")
@mock.patch("cg.meta.backup.backup.BackupAPI.get_first_flow_cell")
@mock.patch("cg.meta.tar.tar.TarAPI")
@mock.patch("cg.store.models.Flowcell")
@mock.patch("cg.store")
def test_fetch_flow_cell_retrieve_next_flow_cell(
    mock_store,
    mock_flow_cell,
    mock_tar,
    mock_get_first_flow_cell,
    mock_get_archived_encryption_key_path,
    mock_get_archived_flow_cell_path,
    mock_create_rta_complete,
    archived_key,
    archived_flow_cell,
    cg_context,
    caplog,
):
    """Tests the fetch_flow_cell method of the backup API when retrieving next flow cell"""

    caplog.set_level(logging.INFO)

    # GIVEN we check if a flow cell needs to be retrieved from PDC
    backup_api = BackupAPI(
        encryption_api=mock.Mock(),
        encrypt_dir=cg_context.backup.encrypt_dir.dict(),
        status=mock_store,
        tar_api=mock_tar,
        pdc_api=mock.Mock(),
        root_dir=cg_context.backup.root.dict(),
    )

    # WHEN no flow cell is specified, but a flow cell in status-db has the status "requested"
    mock_flow_cell.status = FlowCellStatus.REQUESTED
    mock_flow_cell.sequencer_type = Sequencers.NOVASEQ
    backup_api.get_first_flow_cell.return_value = mock_flow_cell
    backup_api.check_processing.return_value = True
    backup_api.get_archived_encryption_key_path.return_value = archived_key
    backup_api.get_archived_flow_cell_path.return_value = archived_flow_cell
    backup_api.tar_api.run_tar_command.return_value = None
    result = backup_api.fetch_flow_cell(flow_cell=None)

    # THEN the process to retrieve the flow cell from PDC is started
    assert "retrieving from PDC" in caplog.text

    # AND when done the status of that flow cell is set to "retrieved"
    assert (
        f"Status for flow cell {mock_get_first_flow_cell.return_value.name} set to "
        f"{FlowCellStatus.RETRIEVED}" in caplog.text
    )
    assert mock_flow_cell.status == "retrieved"

    # AND status-db is updated with the new status
    assert mock_store.session.commit.called

    # AND the elapsed time of the retrieval process is returned
    assert result > 0


@mock.patch("cg.meta.backup.backup.BackupAPI.unlink_files")
@mock.patch("cg.meta.backup.backup.BackupAPI.create_rta_complete")
@mock.patch("cg.meta.backup.backup.BackupAPI.get_archived_flow_cell_path")
@mock.patch("cg.meta.backup.backup.BackupAPI.get_archived_encryption_key_path")
@mock.patch("cg.meta.backup.backup.BackupAPI.check_processing")
@mock.patch("cg.meta.backup.backup.BackupAPI.get_first_flow_cell")
@mock.patch("cg.meta.tar.tar.TarAPI")
@mock.patch("cg.store.models.Flowcell")
@mock.patch("cg.store")
def test_fetch_flow_cell_retrieve_specified_flow_cell(
    mock_store,
    mock_flow_cell,
    mock_tar,
    mock_get_first_flow_cell,
    mock_check_processing,
    mock_get_archived_key,
    mock_get_archived_flow_cell,
    archived_key,
    archived_flow_cell,
    cg_context,
    caplog,
):
    """Tests the fetch_flow_cell method of the backup API when given a flow cell"""

    caplog.set_level(logging.INFO)

    # GIVEN we want to retrieve a specific flow cell from PDC
    backup_api = BackupAPI(
        encryption_api=mock.Mock(),
        encrypt_dir=cg_context.backup.encrypt_dir.dict(),
        status=mock_store,
        tar_api=mock_tar,
        pdc_api=mock.Mock(),
        root_dir=cg_context.backup.root.dict(),
    )
    mock_flow_cell.status = FlowCellStatus.REQUESTED
    mock_flow_cell.sequencer_type = Sequencers.NOVASEQ
    backup_api.check_processing.return_value = True
    backup_api.get_archived_encryption_key_path.return_value = archived_key
    backup_api.get_archived_flow_cell_path.return_value = archived_flow_cell
    backup_api.tar_api.run_tar_command.return_value = None
    result = backup_api.fetch_flow_cell(flow_cell=mock_flow_cell)

    # THEN no flow cell is taken form statusdb
    mock_get_first_flow_cell.assert_not_called()

    # THEN the process to retrieve the flow cell from PDC is started
    assert "retrieving from PDC" in caplog.text

    # AND when done the status of that flow cell is set to "retrieved"
    assert (
        f"Status for flow cell {mock_flow_cell.name} set to {FlowCellStatus.RETRIEVED}"
        in caplog.text
    )
    assert mock_flow_cell.status == "retrieved"

    # AND status-db is updated with the new status
    assert mock_store.session.commit.called

    # AND the elapsed time of the retrieval process is returned
    assert result > 0


@mock.patch("cg.meta.backup.backup.BackupAPI.unlink_files")
@mock.patch("cg.meta.backup.backup.BackupAPI.create_rta_complete")
@mock.patch("cg.meta.backup.backup.BackupAPI.get_archived_flow_cell_path")
@mock.patch("cg.meta.backup.backup.BackupAPI.get_archived_encryption_key_path")
@mock.patch("cg.meta.backup.backup.BackupAPI.check_processing")
@mock.patch("cg.meta.backup.backup.BackupAPI.get_first_flow_cell")
@mock.patch("cg.meta.tar.tar.TarAPI")
@mock.patch("cg.store.models.Flowcell")
@mock.patch("cg.meta.backup.pdc.PdcAPI")
@mock.patch("cg.store")
def test_fetch_flow_cell_pdc_retrieval_failed(
    mock_store,
    mock_pdc,
    mock_flow_cell,
    mock_tar,
    mock_get_first_flow_cell,
    mock_check_processing,
    mock_get_archived_key,
    mock_get_archived_flow_cell,
    archived_key,
    archived_flow_cell,
    cg_context,
    caplog,
):
    """Tests the fetch_flow_cell method of the backup API when PDC retrieval failed"""

    caplog.set_level(logging.INFO)

    # GIVEN we are going to retrieve a flow cell from PDC
    backup_api = BackupAPI(
        encryption_api=mock.Mock(),
        encrypt_dir=cg_context.backup.encrypt_dir.dict(),
        status=mock_store,
        tar_api=mock_tar,
        pdc_api=mock_pdc,
        root_dir=cg_context.backup.root.dict(),
    )
    mock_flow_cell.status = FlowCellStatus.REQUESTED
    mock_flow_cell.sequencer_type = Sequencers.NOVASEQ
    backup_api.check_processing.return_value = True
    backup_api.get_archived_encryption_key_path.return_value = archived_key
    backup_api.get_archived_flow_cell_path.return_value = archived_flow_cell
    backup_api.tar_api.run_tar_command.return_value = None

    # WHEN the retrieval process fails
    mock_pdc.retrieve_file_from_pdc.side_effect = subprocess.CalledProcessError(1, "echo")
    with pytest.raises(subprocess.CalledProcessError):
        backup_api.fetch_flow_cell(flow_cell=mock_flow_cell)

    # THEN the failure to retrieve is logged
    assert "retrieval failed" in caplog.text


@mock.patch("cg.meta.backup.backup.BackupAPI.unlink_files")
@mock.patch("cg.meta.backup.backup.BackupAPI.create_rta_complete")
@mock.patch("cg.meta.backup.backup.BackupAPI.query_pdc_for_flow_cell")
@mock.patch("cg.meta.backup.backup.BackupAPI.get_archived_encryption_key_path")
@mock.patch("cg.meta.backup.backup.BackupAPI.get_archived_flow_cell_path")
@mock.patch("cg.meta.tar.tar.TarAPI")
@mock.patch("cg.store.models.Flowcell")
@mock.patch("cg.store")
def test_fetch_flow_cell_integration(
    mock_store,
    mock_flow_cell,
    mock_tar,
    mock_query,
    archived_key,
    archived_flow_cell,
    cg_context,
    pdc_query,
    caplog,
):
    """Component integration test for the BackupAPI, fetching a specified flow cell"""

    caplog.set_level(logging.INFO)

    # GIVEN we want to retrieve a specific flow cell from PDC
    backup_api = BackupAPI(
        encryption_api=mock.Mock(),
        encrypt_dir=cg_context.backup.encrypt_dir.dict(),
        status=mock_store,
        tar_api=mock_tar,
        pdc_api=mock.Mock(),
        root_dir=cg_context.backup.root.dict(),
    )
    mock_flow_cell.status = FlowCellStatus.REQUESTED
    mock_flow_cell.sequencer_type = Sequencers.NOVASEQ
    mock_store.get_flow_cells_by_statuses.return_value.count.return_value = 0
    mock_query.return_value = pdc_query

    backup_api.tar_api.run_tar_command.return_value = None
    result = backup_api.fetch_flow_cell(flow_cell=mock_flow_cell)

    # THEN the process to retrieve the flow cell from PDC is started
    assert "retrieving from PDC" in caplog.text

    # AND when done the status of that flow cell is set to "retrieved"
    assert (
        f"Status for flow cell {mock_flow_cell.name} set to {FlowCellStatus.RETRIEVED}"
        in caplog.text
    )
    assert mock_flow_cell.status == "retrieved"

    # AND status-db is updated with the new status
    assert mock_store.session.commit.called

    # AND the elapsed time of the retrieval process is returned
    assert result > 0


@mock.patch("cg.meta.backup.backup.SpringBackupAPI.is_spring_file_archived")
@mock.patch("cg.meta.backup.backup.SpringBackupAPI.remove_archived_spring_file")
@mock.patch("cg.meta.backup.backup.SpringBackupAPI.mark_file_as_archived")
@mock.patch("cg.apps.housekeeper.hk.HousekeeperAPI")
@mock.patch("cg.meta.encryption.encryption.SpringEncryptionAPI")
@mock.patch("cg.meta.backup.pdc.PdcAPI")
def test_encrypt_and_archive_spring_file(
    mock_pdc_api: PdcAPI,
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
        encryption_api=mock_spring_encryption_api, hk_api=mock_housekeeper, pdc_api=mock_pdc_api
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
            dry_run=False,
        ),
        call(
            file_path=str(mock_spring_encryption_api.encrypted_key_path.return_value),
            dry_run=False,
        ),
    ]
    mock_pdc_api.archive_file_to_pdc.assert_has_calls(calls)

    # AND the spring file should be marked as archived in Housekeeper
    mock_mark_file_as_archived.assert_called_once_with(spring_file_path)

    # AND the original spring file should be removed
    mock_remove_archived_spring_files.assert_called_once_with(spring_file_path)


@mock.patch("cg.meta.backup.backup.SpringBackupAPI.is_spring_file_archived")
@mock.patch("cg.apps.housekeeper.hk")
@mock.patch("cg.meta.encryption.encryption")
@mock.patch("cg.meta.backup.pdc")
def test_encrypt_and_archive_spring_file_pdc_archiving_failed(
    mock_pdc: PdcAPI,
    mock_spring_encryption_api: SpringEncryptionAPI,
    mock_housekeeper: HousekeeperAPI,
    mock_is_archived,
    spring_file_path,
    caplog,
):
    # GIVEN a spring file that needs to be encrypted and archived to PDC
    spring_backup_api = SpringBackupAPI(
        encryption_api=mock_spring_encryption_api, hk_api=mock_housekeeper, pdc_api=mock_pdc
    )

    # WHEN running the encryption and archiving process, and the encryption command fails
    mock_is_archived.return_value = False
    mock_spring_encryption_api.encrypted_spring_file_path.return_value = (
        spring_file_path.with_suffix(FileExtensions.SPRING + FileExtensions.GPG)
    )
    mock_spring_encryption_api.encrypted_key_path.return_value = spring_file_path.with_suffix(
        FileExtensions.KEY + FileExtensions.GPG
    )
    mock_pdc.archive_file_to_pdc.side_effect = subprocess.CalledProcessError(1, "echo")
    spring_backup_api.encrypt_and_archive_spring_file(spring_file_path=spring_file_path)

    # THEN the appropriate message should be logged and the spring file directory should be
    # cleaned up
    assert "Encryption failed" in caplog.text
    mock_spring_encryption_api.cleanup.assert_called_with(spring_file_path)


@mock.patch("cg.meta.backup.backup.SpringBackupAPI.is_spring_file_archived")
@mock.patch("cg.apps.housekeeper.hk")
@mock.patch("cg.meta.encryption.encryption")
@mock.patch("cg.meta.backup.pdc")
def test_encrypt_and_archive_spring_file_checksum_failed(
    mock_pdc_api: PdcAPI,
    mock_spring_encryption_api: SpringEncryptionAPI,
    mock_housekeeper: HousekeeperAPI,
    mock_is_archived,
    spring_file_path,
    caplog,
):
    # GIVEN a spring file that needs to be encrypted and archived to PDC
    spring_backup_api = SpringBackupAPI(
        encryption_api=mock_spring_encryption_api, hk_api=mock_housekeeper, pdc_api=mock_pdc_api
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
@mock.patch("cg.meta.backup.pdc")
def test_mark_file_as_archived(
    mock_pdc_api: PdcAPI,
    mock_spring_encryption_api: SpringEncryptionAPI,
    mock_housekeeper: HousekeeperAPI,
    spring_file_path,
    caplog,
):
    caplog.set_level(logging.INFO)
    # GIVEN a file
    spring_backup_api = SpringBackupAPI(
        encryption_api=mock_spring_encryption_api, hk_api=mock_housekeeper, pdc_api=mock_pdc_api
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
@mock.patch("cg.meta.backup.pdc")
def test_mark_file_as_archived_dry_run(
    mock_pdc_api: PdcAPI,
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
        pdc_api=mock_pdc_api,
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
@mock.patch("cg.meta.backup.pdc")
def test_decrypt_and_retrieve_spring_file(
    mock_pdc_api: PdcAPI,
    mock_spring_encryption_api: SpringEncryptionAPI,
    mock_housekeeper: HousekeeperAPI,
    spring_file_path,
):
    # GIVEN a spring file that needs to be decrypted and retrieved from PDC
    spring_backup_api = SpringBackupAPI(
        encryption_api=mock_spring_encryption_api, hk_api=mock_housekeeper, pdc_api=mock_pdc_api
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
    mock_pdc_api.retrieve_file_from_pdc.assert_has_calls(calls)


@mock.patch("cg.apps.housekeeper.hk")
@mock.patch("cg.meta.encryption.encryption")
@mock.patch("cg.meta.backup.pdc")
def test_decrypt_and_retrieve_spring_file_pdc_retrieval_failed(
    mock_pdc: PdcAPI,
    mock_spring_encryption_api: SpringEncryptionAPI,
    mock_housekeeper: HousekeeperAPI,
    spring_file_path,
    caplog,
):
    # GIVEN a spring file that needs to be encrypted and archived to PDC
    spring_backup_api = SpringBackupAPI(
        encryption_api=mock_spring_encryption_api, hk_api=mock_housekeeper, pdc_api=mock_pdc
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
