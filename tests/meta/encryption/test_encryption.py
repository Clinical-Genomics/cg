"""Tests for the meta EncryptionAPIs."""

import pathlib

import mock

from cg.meta.encryption.encryption import EncryptionAPI


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
