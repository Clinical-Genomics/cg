"""Tests for the meta EncryptionAPIs."""

import logging
import pathlib
import shutil
from pathlib import Path

import mock
import pytest

from cg.exc import FlowCellEncryptionError, FlowCellError
from cg.meta.encryption.encryption import (
    EncryptionAPI,
    FlowCellEncryptionAPI,
    SpringEncryptionAPI,
)
from cg.models.run_devices.illumina_run_directory_data import IlluminaRunDirectoryData


@mock.patch("cg.utils.Process")
def test_run_gpg_command(mock_process, binary_path: str, test_command: list[str]):
    """Tests the run_gpg_command method"""
    # GIVEN a CLI command input for the Process API
    command = test_command

    # WHEN running that command
    encryption_api = EncryptionAPI(binary_path=binary_path)
    encryption_api.process = mock_process()
    encryption_api.process.binary = binary_path
    encryption_api.run_gpg_command(command=command)

    # THEN the Process API should be used to execute that command with dry_run set to False
    encryption_api.process.run_command.assert_called_once_with(command, dry_run=False)


@mock.patch("cg.utils.Process")
def test_run_gpg_command_dry_run(mock_process, binary_path: str, test_command: list[str]):
    """Tests the run_gpg_command method"""
    # GIVEN a CLI command input for the Process API
    command = test_command

    # WHEN running a gpg command in dry mode
    encryption_api = EncryptionAPI(binary_path=binary_path, dry_run=True)
    encryption_api.process = mock_process()
    encryption_api.run_gpg_command(command=command)

    # THEN the Process API should be used to execute that command with dry_run set to True
    encryption_api.process.run_command.assert_called_once_with(command, dry_run=True)


def test_generate_temporary_passphrase(mocker, binary_path: str):
    """Tests generating a temporary passphrase"""
    # GIVEN an instance of the encryption API
    encryption_api = EncryptionAPI(binary_path=binary_path, dry_run=True)
    mocker.patch("cg.meta.encryption.encryption.EncryptionAPI.run_passhprase_process")

    # WHEN creating a temporary passphrase
    result = encryption_api.generate_temporary_passphrase_file()

    # THEN the passphrase file should be generated as a temporary file
    assert type(result) is pathlib.PosixPath
    assert result.exists()


def test_get_asymmetric_encryption_command(
    binary_path: str,
    input_file_path: Path,
    output_file_path: Path,
    asymmetric_encryption_command: list[str],
):
    """Tests creating the asymmetric encryption command"""
    # GIVEN an input file and an output file for a gpg command
    encryption_api = SpringEncryptionAPI(binary_path=binary_path)

    # WHEN generating the GPG command for asymmetric_encryption
    result = encryption_api.get_asymmetric_encryption_command(
        input_file=input_file_path, output_file=output_file_path
    )

    # THEN the correct parameters should be returned
    assert result == asymmetric_encryption_command


def test_get_asymmetric_decryption_command(
    binary_path: str,
    input_file_path: Path,
    output_file_path: Path,
    asymmetric_decryption_command: list[str],
):
    """Tests creating the asymmetric decryption command"""
    # GIVEN an input file and an output file for a gpg command
    encryption_api = SpringEncryptionAPI(binary_path=binary_path)

    # WHEN generating the GPG command for asymmetric_decryption
    result = encryption_api.get_asymmetric_decryption_command(
        input_file=input_file_path, output_file=output_file_path
    )

    # THEN the correct parameters should be returned
    assert result == asymmetric_decryption_command


@mock.patch("cg.meta.encryption.encryption.SpringEncryptionAPI.generate_temporary_passphrase_file")
def test_get_symmetric_encryption_command(
    mock_passphrase,
    binary_path: str,
    input_file_path: Path,
    output_file_path: Path,
    temporary_passphrase: Path,
    symmetric_encryption_command: list[str],
):
    """Tests creating the symmetric encryption command"""
    # GIVEN an input file and an output file for a gpg command
    encryption_api = SpringEncryptionAPI(binary_path=binary_path)
    mock_passphrase.return_value = temporary_passphrase.as_posix()

    # WHEN generating the GPG command for symmetric_encryption
    result = encryption_api.get_symmetric_encryption_command(
        input_file=input_file_path, output_file=output_file_path
    )

    # THEN the correct parameters should be returned
    assert result == symmetric_encryption_command


def test_get_symmetric_decryption_command(
    binary_path: str,
    input_file_path: Path,
    output_file_path: Path,
    encryption_key_file: str,
    symmetric_decryption_command: list[str],
):
    """Tests creating the symmetric decryption command"""
    # GIVEN an input file and an output file for a gpg command
    encryption_api = SpringEncryptionAPI(binary_path=binary_path)

    # WHEN generating the GPG command for symmetric_decryption
    result = encryption_api.get_symmetric_decryption_command(
        input_file=input_file_path, output_file=output_file_path, encryption_key=encryption_key_file
    )

    # THEN the correct parameters should be returned
    assert result == symmetric_decryption_command


@mock.patch("cg.meta.encryption.encryption.SpringEncryptionAPI.run_gpg_command")
@mock.patch("cg.meta.encryption.encryption.SpringEncryptionAPI.encrypted_spring_file_path")
@mock.patch("cg.meta.encryption.encryption.SpringEncryptionAPI.generate_temporary_passphrase_file")
@mock.patch("cg.utils.Process")
def test_spring_symmetric_encryption(
    mock_process,
    mock_passphrase,
    mock_encrypted_spring_file,
    binary_path: str,
    encrypted_spring_file_path: Path,
    spring_file_path: Path,
    spring_symmetric_encryption_command: list[str],
    temporary_passphrase: Path,
):
    """Tests encrypting a spring file"""
    # GIVEN a spring file
    encryption_api = SpringEncryptionAPI(binary_path=binary_path)
    encryption_api.process = mock_process()
    mock_encrypted_spring_file.return_value = encrypted_spring_file_path
    mock_passphrase.return_value = temporary_passphrase.as_posix()

    # WHEN symmetrically encrypting the spring file
    encryption_api.spring_symmetric_encryption(spring_file_path=spring_file_path)

    # THEN the gpg command should be run with the correct encryption command
    encryption_api.run_gpg_command.assert_called_once_with(spring_symmetric_encryption_command)


@mock.patch("cg.meta.encryption.encryption.SpringEncryptionAPI.run_gpg_command")
@mock.patch("cg.meta.encryption.encryption.SpringEncryptionAPI.encrypted_key_path")
@mock.patch("cg.meta.encryption.encryption.SpringEncryptionAPI.generate_temporary_passphrase_file")
@mock.patch("cg.utils.Process")
def test_key_asymmetric_encryption(
    mock_process,
    mock_passphrase,
    mock_encrypted_key_file,
    binary_path: str,
    encrypted_key_file: Path,
    key_asymmetric_encryption_command: list[str],
    spring_file_path: Path,
    temporary_passphrase: Path,
):
    """Tests encrypting an encryption key"""
    # GIVEN a temporary passphrase
    encryption_api = SpringEncryptionAPI(binary_path=binary_path)
    encryption_api.process = mock_process()
    mock_encrypted_key_file.return_value = encrypted_key_file
    mock_passphrase.return_value = temporary_passphrase.as_posix()

    # WHEN asymmetrically encrypting the temporary passphrase
    encryption_api.key_asymmetric_encryption(spring_file_path=spring_file_path)

    # THEN the gpg command should be run with the correct encryption command
    encryption_api.run_gpg_command.assert_called_once_with(key_asymmetric_encryption_command)


@mock.patch("cg.meta.encryption.encryption.SpringEncryptionAPI.run_gpg_command")
@mock.patch("cg.meta.encryption.encryption.SpringEncryptionAPI.encrypted_spring_file_path")
@mock.patch("cg.utils.Process")
def test_spring_symmetric_decryption(
    mock_process,
    mock_encrypted_spring_file_path,
    binary_path: str,
    encrypted_spring_file_path: Path,
    spring_symmetric_decryption_command: list[str],
    spring_file_path: Path,
):
    """Tests decrypting a spring file"""
    # GIVEN an encrypted spring file
    encryption_api = SpringEncryptionAPI(binary_path=binary_path)
    encryption_api.process = mock_process()
    mock_encrypted_spring_file_path.return_value = encrypted_spring_file_path

    # WHEN symmetrically decrypting the spring file
    encryption_api.spring_symmetric_decryption(
        spring_file_path=spring_file_path, output_file=spring_file_path
    )

    # THEN the gpg command should be run with the correct decryption command
    encryption_api.run_gpg_command.assert_called_once_with(spring_symmetric_decryption_command)


@mock.patch("cg.meta.encryption.encryption.SpringEncryptionAPI.run_gpg_command")
@mock.patch("cg.meta.encryption.encryption.SpringEncryptionAPI.encrypted_key_path")
@mock.patch("cg.utils.Process")
def test_key_asymmetric_decryption(
    mock_process,
    mock_encrypted_key_file,
    binary_path: str,
    encrypted_key_file: Path,
    key_asymmetric_decryption_command: list[str],
    spring_file_path: Path,
):
    """Tests decrypting a encryption key file"""
    # GIVEN an encryption encryption key
    encryption_api = SpringEncryptionAPI(binary_path=binary_path)
    encryption_api.process = mock_process()
    mock_encrypted_key_file.return_value = encrypted_key_file

    # WHEN asymmetrically decrypting the encryption key
    encryption_api.key_asymmetric_decryption(spring_file_path=spring_file_path)

    # THEN the gpg command should be run with the correct decryption command
    encryption_api.run_gpg_command.assert_called_once_with(key_asymmetric_decryption_command)


@mock.patch("pathlib.Path.unlink")
@mock.patch("cg.utils.Process")
def test_cleanup_all_files(
    mock_process, mock_unlink, binary_path: str, spring_file_path: Path, caplog
):
    """ """
    # GIVEN there are files to clean up: decrypted spring file, encrypted spring file, encrypted
    # encryption key and encryption key
    caplog.set_level(logging.INFO)
    encryption_api = SpringEncryptionAPI(binary_path=binary_path)
    encryption_api.process = mock_process()

    # WHEN attempting to clean up those files
    encryption_api.cleanup(spring_file_path=spring_file_path)

    # THEN the files should be removed and the result logged
    assert 4 == mock_unlink.call_count
    assert "Removed existing decrypted checksum spring file" in caplog.text
    assert "Removed existing encrypted spring file" in caplog.text
    assert "Removed existing encrypted key file" in caplog.text
    assert "Removed existing key file" in caplog.text


@mock.patch("pathlib.Path.unlink")
@mock.patch("cg.utils.Process")
def test_cleanup_no_files(
    mock_process,
    mock_unlink,
    binary_path: str,
    spring_file_path: Path,
    caplog,
):
    """ """
    # GIVEN there are no files out of a possible four to clean up
    caplog.set_level(logging.INFO)
    encryption_api = SpringEncryptionAPI(binary_path=binary_path)
    encryption_api.process = mock_process()
    mock_unlink.side_effect = [
        FileNotFoundError,
        FileNotFoundError,
        FileNotFoundError,
        FileNotFoundError,
    ]
    # WHEN attempting to clean up those files
    encryption_api.cleanup(spring_file_path=spring_file_path)

    # THEN the cleanup method should handle the thrown exception and log the result
    assert 4 == mock_unlink.call_count
    assert "No decrypted checksum spring file to clean up, continuing cleanup" in caplog.text
    assert "No encrypted spring file to clean up, continuing cleanup" in caplog.text
    assert "No encrypted key file to clean up, continuing cleanup" in caplog.text
    assert "No existing key file to clean up, cleanup process completed" in caplog.text


def test_flow_cell_encryption_api(flow_cell_encryption_api: FlowCellEncryptionAPI):
    """Tests instantiating flow cell encryption API."""
    # GIVEN a FlowCellEncryptionAPI

    # WHEN instantiating the API

    # THEN return a FlowCellEncryptionAPI object
    assert isinstance(flow_cell_encryption_api, FlowCellEncryptionAPI)


def test_get_flow_cell_symmetric_encryption_command(
    flow_cell_encryption_api: FlowCellEncryptionAPI,
    output_file_path: Path,
    temporary_passphrase: Path,
):
    # GIVEN a FlowCellEncryptionAPI

    # WHEN getting the command
    command: str = flow_cell_encryption_api.get_flow_cell_symmetric_encryption_command(
        output_file=output_file_path, passphrase_file_path=temporary_passphrase
    )

    # THEN return a string
    assert isinstance(command, str)


def test_get_flow_cell_symmetric_decryption_command(
    flow_cell_encryption_api: FlowCellEncryptionAPI,
    input_file_path: Path,
    temporary_passphrase: Path,
):
    # GIVEN a FlowCellEncryptionAPI

    # WHEN getting the command
    command: str = flow_cell_encryption_api.get_flow_cell_symmetric_decryption_command(
        input_file=input_file_path, passphrase_file_path=temporary_passphrase
    )

    # THEN return a string
    assert isinstance(command, str)


def test_create_pending_file(
    flow_cell_encryption_api: FlowCellEncryptionAPI,
):
    # GIVEN a FlowCellEncryptionAPI

    # WHEN checking if encryption is possible
    flow_cell_encryption_api.flow_cell_encryption_dir.mkdir(parents=True)
    flow_cell_encryption_api.dry_run = False
    flow_cell_encryption_api.create_pending_file(
        pending_path=flow_cell_encryption_api.pending_file_path
    )

    # THEN pending file should exist
    assert flow_cell_encryption_api.pending_file_path.exists()

    # Clean-up
    shutil.rmtree(flow_cell_encryption_api.flow_cell_encryption_dir)


def test_create_pending_file_when_dry_run(
    flow_cell_encryption_api: FlowCellEncryptionAPI,
):
    # GIVEN a FlowCellEncryptionAPI

    # WHEN checking if encryption is possible
    flow_cell_encryption_api.create_pending_file(
        pending_path=flow_cell_encryption_api.pending_file_path
    )

    # THEN pending file should not exist
    assert not flow_cell_encryption_api.pending_file_path.exists()


def test_is_encryption_possible(flow_cell_encryption_api: FlowCellEncryptionAPI, mocker):
    # GIVEN a FlowCellEncryptionAPI

    # GIVEN that sequencing is ready
    mocker.patch.object(IlluminaRunDirectoryData, "is_sequencing_run_ready")
    IlluminaRunDirectoryData.is_sequencing_run_ready.return_value = True

    # WHEN checking if encryption is possible
    is_possible: bool = flow_cell_encryption_api.is_encryption_possible()

    # THEN return True
    assert is_possible


def test_is_encryption_possible_when_sequencing_not_ready(
    caplog, flow_cell_encryption_api: FlowCellEncryptionAPI, flow_cell_name: str, mocker
):
    caplog.set_level(logging.ERROR)

    # GIVEN a FlowCellEncryptionAPI

    # GIVEN that sequencing is not ready
    mocker.patch.object(IlluminaRunDirectoryData, "is_sequencing_run_ready")
    IlluminaRunDirectoryData.is_sequencing_run_ready.return_value = False

    # WHEN checking if encryption is possible
    with pytest.raises(FlowCellError):
        flow_cell_encryption_api.is_encryption_possible()

        # THEN error should be raised
        assert f"Flow cell: {flow_cell_name} is not ready" in caplog.text


def test_is_encryption_possible_when_encryption_is_completed(
    caplog, flow_cell_encryption_api: FlowCellEncryptionAPI, flow_cell_name: str, mocker
):
    # GIVEN a FlowCellEncryptionAPI

    # GIVEN that sequencing is ready
    mocker.patch.object(IlluminaRunDirectoryData, "is_sequencing_run_ready")
    IlluminaRunDirectoryData.is_sequencing_run_ready.return_value = True

    # GIVEN that encryption is completed
    flow_cell_encryption_api.flow_cell_encryption_dir.mkdir(parents=True)
    flow_cell_encryption_api.complete_file_path.touch()

    # WHEN checking if encryption is possible
    with pytest.raises(FlowCellEncryptionError):
        flow_cell_encryption_api.is_encryption_possible()

        # THEN error should be raised
        assert f"Encryption already completed for flow cell: {flow_cell_name}" in caplog.text

    # Clean-up
    shutil.rmtree(flow_cell_encryption_api.flow_cell_encryption_dir)


def test_is_encryption_possible_when_encryption_is_pending(
    caplog, flow_cell_encryption_api: FlowCellEncryptionAPI, flow_cell_name: str, mocker
):
    # GIVEN a FlowCellEncryptionAPI

    # GIVEN that sequencing is ready
    mocker.patch.object(IlluminaRunDirectoryData, "is_sequencing_run_ready")
    IlluminaRunDirectoryData.is_sequencing_run_ready.return_value = True

    # GIVEN that encryption is pending
    flow_cell_encryption_api.flow_cell_encryption_dir.mkdir(parents=True)
    flow_cell_encryption_api.pending_file_path.touch()

    # WHEN checking if encryption is possible
    with pytest.raises(FlowCellEncryptionError):
        flow_cell_encryption_api.is_encryption_possible()

        # THEN error should be raised
        assert f"Encryption already started for flow cell: {flow_cell_name}" in caplog.text

    # Clean-up
    shutil.rmtree(flow_cell_encryption_api.flow_cell_encryption_dir)


def test_encrypt_flow_cell(
    caplog, flow_cell_encryption_api: FlowCellEncryptionAPI, mocker, sbatch_job_number: int
):
    caplog.set_level(logging.INFO)
    # GIVEN a FlowCellEncryptionAPI

    # GIVEN that sequencing is ready
    mocker.patch.object(IlluminaRunDirectoryData, "is_sequencing_run_ready")
    IlluminaRunDirectoryData.is_sequencing_run_ready.return_value = True

    # WHEN encrypting flow cell
    flow_cell_encryption_api.encrypt_flow_cell()

    # THEN sbatch should be submitted
    assert f"Flow cell encryption running as job {sbatch_job_number}" in caplog.text


def test_start_encryption(
    caplog, flow_cell_encryption_api: FlowCellEncryptionAPI, mocker, sbatch_job_number: int
):
    caplog.set_level(logging.INFO)
    # GIVEN a FlowCellEncryptionAPI

    # GIVEN that sequencing is ready
    mocker.patch.object(IlluminaRunDirectoryData, "is_sequencing_run_ready")
    IlluminaRunDirectoryData.is_sequencing_run_ready.return_value = True

    # WHEN trying to start encrypting flow cell
    flow_cell_encryption_api.start_encryption()

    # THEN sbatch should be submitted
    assert f"Flow cell encryption running as job {sbatch_job_number}" in caplog.text
