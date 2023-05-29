"""Tests for the meta EncryptionAPI and SpringEncryptionAPI"""
import logging
import pathlib

import mock
import pytest

from cg.exc import ChecksumFailedError
from cg.meta.encryption.encryption import EncryptionAPI, SpringEncryptionAPI


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


def test_generate_temporary_passphrase(mocker, binary_path):
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
    binary_path, input_file, output_file, asymmetric_encryption_command
):
    """Tests creating the asymmetric encryption command"""
    # GIVEN an input file and an output file for a gpg command
    encryption_api = SpringEncryptionAPI(binary_path=binary_path)

    # WHEN generating the GPG command for asymmetric_encryption
    result = encryption_api.get_asymmetric_encryption_command(
        input_file=input_file, output_file=output_file
    )

    # THEN the correct parameters should be returned
    assert result == asymmetric_encryption_command


def test_get_asymmetric_decryption_command(
    binary_path, input_file, output_file, asymmetric_decryption_command
):
    """Tests creating the asymmetric decryption command"""
    # GIVEN an input file and an output file for a gpg command
    encryption_api = SpringEncryptionAPI(binary_path=binary_path)

    # WHEN generating the GPG command for asymmetric_decryption
    result = encryption_api.get_asymmetric_decryption_command(
        input_file=input_file, output_file=output_file
    )

    # THEN the correct parameters should be returned
    assert result == asymmetric_decryption_command


@mock.patch("cg.meta.encryption.encryption.SpringEncryptionAPI.generate_temporary_passphrase_file")
def test_get_symmetric_encryption_command(
    mock_passphrase,
    binary_path,
    input_file,
    output_file,
    temporary_passphrase,
    symmetric_encryption_command,
):
    """Tests creating the symmetric encryption command"""
    # GIVEN an input file and an output file for a gpg command
    encryption_api = SpringEncryptionAPI(binary_path=binary_path)
    mock_passphrase.return_value = temporary_passphrase

    # WHEN generating the GPG command for symmetric_encryption
    result = encryption_api.get_symmetric_encryption_command(
        input_file=input_file, output_file=output_file
    )

    # THEN the correct parameters should be returned
    assert result == symmetric_encryption_command


def test_get_symmetric_decryption_command(
    binary_path, input_file, output_file, encryption_key_file, symmetric_decryption_command
):
    """Tests creating the symmetric decryption command"""
    # GIVEN an input file and an output file for a gpg command
    encryption_api = SpringEncryptionAPI(binary_path=binary_path)

    # WHEN generating the GPG command for symmetric_decryption
    result = encryption_api.get_symmetric_decryption_command(
        input_file=input_file, output_file=output_file, encryption_key=encryption_key_file
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
    binary_path,
    encrypted_spring_file_path,
    spring_file_path,
    spring_symmetric_encryption_command,
    temporary_passphrase,
):
    """Tests encrypting a spring file"""
    # GIVEN a spring file
    encryption_api = SpringEncryptionAPI(binary_path=binary_path)
    encryption_api.process = mock_process()
    mock_encrypted_spring_file.return_value = encrypted_spring_file_path
    mock_passphrase.return_value = temporary_passphrase

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
    binary_path,
    encrypted_key_file,
    key_asymmetric_encryption_command,
    spring_file_path,
    temporary_passphrase,
):
    """Tests encrypting an encryption key"""
    # GIVEN a temporary passphrase
    encryption_api = SpringEncryptionAPI(binary_path=binary_path)
    encryption_api.process = mock_process()
    mock_encrypted_key_file.return_value = encrypted_key_file
    mock_passphrase.return_value = temporary_passphrase

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
    binary_path,
    encrypted_spring_file_path,
    spring_symmetric_decryption_command,
    spring_file_path,
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
    binary_path,
    encrypted_key_file,
    key_asymmetric_decryption_command,
    spring_file_path,
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
def test_cleanup_all_files(mock_process, mock_unlink, binary_path, spring_file_path, caplog):
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
    binary_path,
    spring_file_path,
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
