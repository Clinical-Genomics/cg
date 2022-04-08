import pathlib
from pathlib import Path

import mock

from cg.meta.encryption.encryption import EncryptionAPI, SpringEncryptionAPI


@mock.patch("cg.utils.Process")
def test_run_gpg_command(mock_process, binary_path):
    # GIVEN
    encryption_api = EncryptionAPI(binary_path=binary_path, dry_run=False)
    encryption_api.process = mock_process()

    # WHEN running a gpg command
    encryption_api.run_gpg_command(command=["test", "command"])

    # THEN the Process API should be used to execute that command with dry_run set to False
    encryption_api.process.run_command.assert_called_once_with(["test", "command"], dry_run=False)


@mock.patch("cg.utils.Process")
def test_run_gpg_command_dry_run(mock_process, binary_path):
    # GIVEN
    encryption_api = EncryptionAPI(binary_path=binary_path, dry_run=True)
    encryption_api.process = mock_process()

    # WHEN running a gpg command in dry mode
    encryption_api.run_gpg_command(command=["test", "command"])

    # THEN the Process API should be used to execute that command with dry_run set to True
    encryption_api.process.run_command.assert_called_once_with(["test", "command"], dry_run=True)


@mock.patch("cg.utils.Process")
def test_generate_temporary_passphrase(mock_process, binary_path):
    # GIVEN
    encryption_api = EncryptionAPI(binary_path=binary_path, dry_run=True)
    encryption_api.process = mock_process()

    # WHEN creating a temporary passphrase
    result = encryption_api.generate_temporary_passphrase_file()
    # THEN the passphrase file should be a temporary file
    assert type(result) is pathlib.PosixPath
    assert result.parent == Path("/tmp")
    assert result.name.startswith("tmp")


def test_output_input_parameters(binary_path, input_file, output_file):
    # GIVEN an input file and an output file for a gpg command
    encryption_api = EncryptionAPI(binary_path=binary_path)

    # WHEN generating the output/input parameters for a GPG command
    result = encryption_api.output_input_parameters(input_file=input_file, output_file=output_file)

    # THEN the result should be a list of the form ["-o", str(output_file), str(input_file)]
    assert result == ["-o", str(output_file), str(input_file)]


def test_asymmetric_encryption_command(binary_path, input_file, output_file):
    # GIVEN an input file and an output file for a gpg command
    encryption_api = SpringEncryptionAPI(binary_path=binary_path)

    # WHEN generating the GPG command for asymmetric_encryption
    result = encryption_api.asymmetric_encryption_command(
        input_file=input_file, output_file=output_file
    )

    # THEN the result should be [ "--encrypt", "--recipient", "Clinical Genomics", "-o",
    # str(output_file), str(input_file)]
    assert result == [
        "--encrypt",
        "--recipient",
        "Clinical Genomics",
        "-o",
        str(output_file),
        str(input_file),
    ]


def test_asymmetric_decryption_command(binary_path, input_file, output_file):
    # GIVEN an input file and an output file for a gpg command
    encryption_api = SpringEncryptionAPI(binary_path=binary_path)

    # WHEN generating the GPG command for asymmetric_decryption
    result = encryption_api.asymmetric_decryption_command(
        input_file=input_file, output_file=output_file
    )

    # THEN the result should be  ["--decrypt", "--batch", "--cipher-algo", "AES256",
    # "--passphrase", "-o", str(output_file), str(input_file)]
    assert result == [
        "--decrypt",
        "--batch",
        "--cipher-algo",
        "AES256",
        "--passphrase",
        "Clinical Genomics",
        "-o",
        str(output_file),
        str(input_file),
    ]


@mock.patch("cg.meta.encryption.encryption.SpringEncryptionAPI.generate_temporary_passphrase_file")
def test_symmetric_encryption_command(
    mock_passphrase, binary_path, input_file, output_file, temporary_passphrase
):
    # GIVEN an input file and an output file for a gpg command
    encryption_api = SpringEncryptionAPI(binary_path=binary_path)
    mock_passphrase.return_value = temporary_passphrase

    # WHEN generating the GPG command for symmetric_encryption
    result = encryption_api.symmetric_encryption_command(
        input_file=input_file, output_file=output_file
    )

    # THEN the result should be correct
    assert encryption_api.temporary_passphrase == temporary_passphrase
    assert result == [
        "--symmetric",
        "--cipher-algo",
        "AES256",
        "--batch",
        "--compress-algo",
        "None",
        "--passphrase-file",
        temporary_passphrase,
        "-o",
        str(output_file),
        str(input_file),
    ]


def test_symmetric_decryption_command(binary_path, input_file, output_file):
    # GIVEN an input file and an output file for a gpg command
    encryption_api = SpringEncryptionAPI(binary_path=binary_path)
    encryption_key = Path("encryption.key")

    # WHEN generating the GPG command for symmetric_decryption
    result = encryption_api.symmetric_decryption_command(
        input_file=input_file, output_file=output_file, encryption_key=encryption_key
    )

    # THEN the result should be correct
    assert result == [
        "--decrypt",
        "--cipher-algo",
        "AES256",
        "--batch",
        "--passphrase-file",
        str(encryption_key),
        "-o",
        str(output_file),
        str(input_file),
    ]


@mock.patch("cg.meta.encryption.encryption.SpringEncryptionAPI.run_gpg_command")
@mock.patch("cg.meta.encryption.encryption.SpringEncryptionAPI.encrypted_spring_file_path")
@mock.patch("cg.meta.encryption.encryption.SpringEncryptionAPI.symmetric_encryption_command")
@mock.patch("cg.utils.Process")
def test_spring_symmetric_encryption(
    mock_process, mock_command, mock_encrypted_spring_file, binary_path, temporary_passphrase
):
    # GIVEN an input file and an output file for a gpg command
    encryption_api = SpringEncryptionAPI(binary_path=binary_path)
    encryption_api.process = mock_process()
    mock_encrypted_spring_file.return_value = Path("/path/to/file.spring.gpg")
    spring_file_path = Path("/path/to/file.spring")
    mock_command.return_value = [
        "--symmetric",
        "--cipher-algo",
        "AES256",
        "--batch",
        "--compress-algo",
        "None",
        "--passphrase-file",
        temporary_passphrase,
        "-o",
        str(mock_encrypted_spring_file),
        str(spring_file_path),
    ]
    spring_file_path = Path("/path/to/file.spring")

    # WHEN generating the GPG command for symmetric_encryption
    encryption_api.spring_symmetric_encryption(spring_file_path=spring_file_path)

    # THEN the result should be correct
    encryption_api.run_gpg_command.assert_called_once_with(mock_command.return_value)
