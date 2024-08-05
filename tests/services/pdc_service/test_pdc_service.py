"""Tests for the meta PdcAPI"""

from unittest import mock
import pytest
from cg.constants import EXIT_FAIL
from cg.constants.process import EXIT_WARNING
from cg.exc import (
    PdcError,
)
from cg.models.cg_config import CGConfig
from tests.conftest import create_process_response


def test_validate_is_dsmc_process_running(cg_context: CGConfig):
    """Tests checking if a Dsmc process is running when no Dsmc process is running."""
    # GIVEN an instance of the PDC API
    pdc_service = cg_context.pdc_service

    # GIVEN no Dsmc process is running

    # WHEN checking if Dsmc is running
    is_dmsc_running: bool = pdc_service.validate_is_dsmc_running()

    # THEN return false
    assert not is_dmsc_running


@mock.patch("cg.utils.commands.Process.run_command")
def test_archive_file_to_pdc(mock_process, cg_context: CGConfig, backup_file_path):
    """Tests execution command to archive file to PDC"""
    # GIVEN an instance of the PDC API

    pdc_service = cg_context.pdc_service
    pdc_service.process = mock_process

    # WHEN archiving a file to PDC
    pdc_service.archive_file_to_pdc(backup_file_path)

    # THEN a dsmc process should be started with the parameter 'archive'
    pdc_service.process.run_command.assert_called_once_with(
        parameters=["archive", backup_file_path], dry_run=False
    )


@mock.patch("cg.utils.commands.Process.run_command")
def test_query_pdc(mock_process, cg_context: CGConfig, backup_file_path):
    """Tests execution command to query files to PDC"""
    # GIVEN an instance of the PDC API
    pdc_service = cg_context.pdc_service
    pdc_service.process = mock_process

    # WHEN querying PDC
    pdc_service.query_pdc(backup_file_path)

    # THEN a dsmc process should be started with parameters 'q archive'
    mock_process.run_command.assert_called_once_with(
        parameters=["q", "archive", backup_file_path], dry_run=False
    )


@mock.patch("cg.utils.commands.Process.run_command")
def test_retrieve_file_from_pdc(mock_process, cg_context: CGConfig, backup_file_path):
    """Tests execution command to retrieve files from PDC"""
    # GIVEN an instance of the PDC API
    pdc_service = cg_context.pdc_service
    pdc_service.process = mock_process

    # WHEN retrieving a file form PDC
    pdc_service.retrieve_file_from_pdc(backup_file_path)

    # THEN a dsmc process should be started with parameters 'retrieve -replace=yes'
    mock_process.run_command.assert_called_once_with(
        parameters=["retrieve", "-replace=yes", backup_file_path], dry_run=False
    )


def test_run_dsmc_command_fail(cg_context: CGConfig):
    """Test that non-zero, non-warning exit-codes raise an error."""
    # GIVEN an instance of the PDC API
    pdc_service = cg_context.pdc_service

    # GIVEN an exit code signifying failure
    with pytest.raises(PdcError), mock.patch(
        "cg.utils.commands.subprocess.run",
        return_value=create_process_response(return_code=EXIT_FAIL),
    ):
        # WHEN running a dsmc command
        pdc_service.run_dsmc_command(["archive", "something"])

        # THEN the appropriate error should have been raised


def test_run_dsmc_command_warning(cg_context: CGConfig, caplog):
    """Test that warning exit-codes do not raise an error."""
    # GIVEN an instance of the PDC API
    pdc_service = cg_context.pdc_service

    # GIVEN an exit code signifying a warning
    with mock.patch(
        "cg.utils.commands.subprocess.run",
        return_value=create_process_response(return_code=EXIT_WARNING),
    ):
        # WHEN running a dsmc command
        pdc_service.run_dsmc_command(["archive", "something"])

    # THEN the warning should have been logged
    assert "WARNING" in caplog.text
