"""Tests for the meta PdcAPI"""
from unittest import mock

from cg.meta.backup.pdc import PdcAPI


@mock.patch("cg.meta.backup.pdc.Process")
def test_archive_file_to_pdc(mock_process):
    """tests execution command to archive files to pdc"""
    # GIVEN
    pdc_api = PdcAPI(binary_path="/usr/bin/echo")
    pdc_api.process = mock_process

    # WHEN
    pdc_api.archive_file_to_pdc("path/to/file")

    # THEN
    mock_process.run_command.assert_called_once_with(
        parameters=["archive", "path/to/file"], dry_run=False
    )


@mock.patch("cg.meta.backup.pdc.Process")
def test_query_pdc(mock_process):
    """tests execution command to archive files to pdc"""
    # GIVEN
    pdc_api = PdcAPI(binary_path="/usr/bin/echo")
    pdc_api.process = mock_process

    # WHEN
    pdc_api.query_pdc("path/to/file")

    # THEN
    mock_process.run_command.assert_called_once_with(
        parameters=["q", "archive", "path/to/file"], dry_run=False
    )


@mock.patch("cg.meta.backup.pdc.Process")
def test_retrieve_file_from_pdc(mock_process):
    """tests execution command to archive files to pdc"""
    # GIVEN
    pdc_api = PdcAPI(binary_path="/usr/bin/echo")
    pdc_api.process = mock_process

    # WHEN
    pdc_api.retrieve_file_from_pdc("path/to/file")

    # THEN
    mock_process.run_command.assert_called_once_with(
        parameters=["retrieve", "--replace=yes", "path/to/file"], dry_run=False
    )
