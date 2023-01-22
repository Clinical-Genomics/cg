"""Tests for the meta PdcAPI"""
from unittest import mock

from cg.meta.backup.pdc import PdcAPI


@mock.patch("cg.meta.backup.pdc.Process")
def test_archive_file_to_pdc(mock_process, binary_path, backup_file_path):
    """Tests execution command to archive file to PDC"""
    # GIVEN an instance of the PDC API
    pdc_api = PdcAPI(binary_path=binary_path)
    pdc_api.process = mock_process

    # WHEN archiving a file to PDC
    pdc_api.archive_file_to_pdc(backup_file_path)

    # THEN a dsmc process should be started with the parameter 'archive'
    mock_process.run_command.assert_called_once_with(
        parameters=["archive", backup_file_path], dry_run=False
    )


@mock.patch("cg.meta.backup.pdc.Process")
def test_query_pdc(mock_process, binary_path, backup_file_path):
    """Tests execution command to query files to PDC"""
    # GIVEN an instance of the PDC API
    pdc_api = PdcAPI(binary_path=binary_path)
    pdc_api.process = mock_process

    # WHEN querying PDC
    pdc_api.query_pdc(backup_file_path)

    # THEN a dsmc process should be started with parameters 'q archive'
    mock_process.run_command.assert_called_once_with(parameters=["q", "archive", backup_file_path])


@mock.patch("cg.meta.backup.pdc.Process")
def test_retrieve_file_from_pdc(mock_process, binary_path, backup_file_path):
    """Tests execution command to retrieve files from PDC"""
    # GIVEN an instance of the PDC API
    pdc_api = PdcAPI(binary_path=binary_path)
    pdc_api.process = mock_process

    # WHEN retrieving a file form PDC
    pdc_api.retrieve_file_from_pdc(backup_file_path)

    # THEN a dsmc process should be started with parameters 'retrieve -replace=yes'
    mock_process.run_command.assert_called_once_with(
        parameters=["retrieve", "-replace=yes", backup_file_path], dry_run=False
    )
