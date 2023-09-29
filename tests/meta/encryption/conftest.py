from pathlib import Path
from typing import List

import pytest

from cg.constants.encryption import EncryptionUserID


@pytest.fixture(name="input_file")
def input_file_path() -> Path:
    """input file"""
    return Path("path", "to", "input.file")


@pytest.fixture(name="output_file")
def output_file_path() -> Path:
    """output file"""
    return Path("path", "to", "output.file")


@pytest.fixture(name="temporary_passphrase")
def temporary_passphrase() -> str:
    """temporary passphrase file"""
    return Path("tmp", "tmp_test_passphrase").as_posix()


@pytest.fixture(name="test_command")
def test_command() -> List:
    """Return a CLI command in the list format required by the Process API"""
    return ["test", "command"]


@pytest.fixture(name="encryption_key_file")
def encryption_key_file() -> Path:
    """Return an encryption key file Path object"""
    return Path("path", "to", "file.key")


@pytest.fixture(name="encrypted_key_file")
def encrypted_key_file() -> Path:
    """Return an encrypted encryption key file Path object"""
    return Path("path", "to", "encryption.key.gpg")


@pytest.fixture(name="spring_file_path")
def spring_file_path() -> Path:
    """Return a spring file Path object"""
    return Path("path", "to", "file.spring")


@pytest.fixture
def encrypted_spring_file_path() -> Path:
    """Return an encrypted spring file Path object"""
    return Path("path", "to", "file.spring.gpg")


@pytest.fixture
def cipher_algorithm() -> str:
    """Cipher algorithm fixture"""
    return "AES256"


@pytest.fixture
def asymmetric_encryption_command(output_file, input_file) -> List:
    """Asymmetric encryption_command fixture"""
    return [
        "--encrypt",
        "--recipient",
        EncryptionUserID.HASTA_USER_ID,
        "-o",
        str(output_file),
        str(input_file),
    ]


@pytest.fixture(name="asymmetric_decryption_command")
def asymmetric_decryption_command(cipher_algorithm, output_file, input_file) -> List:
    """Asymmetric decryption_command fixture"""
    return [
        "--decrypt",
        "--batch",
        "--cipher-algo",
        cipher_algorithm,
        "--passphrase",
        EncryptionUserID.HASTA_USER_ID,
        "-o",
        str(output_file),
        str(input_file),
    ]


@pytest.fixture(name="symmetric_encryption_command")
def symmetric_encryption_command(
    temporary_passphrase, input_file, output_file, spring_file_path, cipher_algorithm
) -> List:
    """Symmetric encryption_command fixture"""
    return [
        "--symmetric",
        "--cipher-algo",
        cipher_algorithm,
        "--batch",
        "--compress-algo",
        "None",
        "--passphrase-file",
        temporary_passphrase,
        "-o",
        str(output_file),
        str(input_file),
    ]


@pytest.fixture(name="symmetric_decryption_command")
def symmetric_decryption_command(
    cipher_algorithm,
    encryption_key_file,
    input_file,
    output_file,
) -> List:
    """Symmetric decryption_command fixture"""
    return [
        "--decrypt",
        "--cipher-algo",
        cipher_algorithm,
        "--batch",
        "--passphrase-file",
        str(encryption_key_file),
        "-o",
        str(output_file),
        str(input_file),
    ]


@pytest.fixture(name="spring_symmetric_encryption_command")
def spring_symmetric_encryption_command(
    temporary_passphrase, encrypted_spring_file_path, spring_file_path, cipher_algorithm
) -> List:
    """Symmetric encryption_command fixture"""
    return [
        "--symmetric",
        "--cipher-algo",
        cipher_algorithm,
        "--batch",
        "--compress-algo",
        "None",
        "--passphrase-file",
        temporary_passphrase,
        "-o",
        str(encrypted_spring_file_path),
        str(spring_file_path),
    ]


@pytest.fixture(name="key_asymmetric_encryption_command")
def key_asymmetric_encryption_command(encrypted_key_file, temporary_passphrase) -> List:
    """Asymmetric encryption_command fixture"""
    return [
        "--encrypt",
        "--recipient",
        EncryptionUserID.HASTA_USER_ID,
        "-o",
        str(encrypted_key_file),
        str(temporary_passphrase),
    ]


@pytest.fixture(name="spring_symmetric_decryption_command")
def spring_symmetric_decryption_command(
    cipher_algorithm,
    encryption_key_file,
    spring_file_path,
    encrypted_spring_file_path,
) -> List:
    """Symmetric decryption_command fixture"""
    return [
        "--decrypt",
        "--cipher-algo",
        cipher_algorithm,
        "--batch",
        "--passphrase-file",
        str(encryption_key_file),
        "-o",
        str(spring_file_path),
        str(encrypted_spring_file_path),
    ]


@pytest.fixture(name="key_asymmetric_decryption_command")
def key_asymmetric_decryption_command(
    cipher_algorithm, encrypted_key_file, encryption_key_file
) -> List:
    """Asymmetric encryption_command fixture"""
    return [
        "--decrypt",
        "--batch",
        "--cipher-algo",
        cipher_algorithm,
        "--passphrase",
        EncryptionUserID.HASTA_USER_ID,
        "-o",
        str(encryption_key_file),
        str(encrypted_key_file),
    ]
