"""Tests for the meta EncryptionAPI."""

import mock

from cg.meta.encryption.encryption import EncryptionAPI


@mock.patch("cg.utils.Process")
def test_run_gpg_command(mock_process, binary_path, test_command):
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
def test_run_gpg_command_dry_run(mock_process, binary_path, test_command):
    """Tests the run_gpg_command method"""
    # GIVEN a CLI command input for the Process API
    command = test_command

    # WHEN running a gpg command in dry mode
    encryption_api = EncryptionAPI(binary_path=binary_path, dry_run=True)
    encryption_api.process = mock_process()
    encryption_api.run_gpg_command(command=command)

    # THEN the Process API should be used to execute that command with dry_run set to True
    encryption_api.process.run_command.assert_called_once_with(command, dry_run=True)


def test_get_asymmetric_decryption_command(
    binary_path, input_file, output_file, asymmetric_decryption_command
):
    """Tests creating the asymmetric decryption command"""
    # GIVEN an input file and an output file for a gpg command
    encryption_api = EncryptionAPI(binary_path=binary_path)

    # WHEN generating the GPG command for asymmetric_decryption
    result = encryption_api.get_asymmetric_decryption_command(
        input_file=input_file, output_file=output_file
    )

    # THEN the correct parameters should be returned
    assert result == asymmetric_decryption_command


def test_get_symmetric_decryption_command(
    binary_path, input_file, output_file, encryption_key_file, symmetric_decryption_command
):
    """Tests creating the symmetric decryption command"""
    # GIVEN an input file and an output file for a gpg command
    encryption_api = EncryptionAPI(binary_path=binary_path)

    # WHEN generating the GPG command for symmetric_decryption
    result = encryption_api.get_symmetric_decryption_command(
        input_file=input_file, output_file=output_file, encryption_key=encryption_key_file
    )

    # THEN the correct parameters should be returned
    assert result == symmetric_decryption_command
