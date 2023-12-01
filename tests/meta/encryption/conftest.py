from pathlib import Path

import pytest

from cg.constants.encryption import CipherAlgorithm, EncryptionUserID


@pytest.fixture
def input_file_path() -> Path:
    return Path("path", "to", "input.file")


@pytest.fixture
def output_file_path() -> Path:
    return Path("path", "to", "output.file")


@pytest.fixture
def temporary_passphrase() -> Path:
    return Path("tmp", "tmp_test_passphrase")


@pytest.fixture
def test_command() -> list[str]:
    """Return a CLI command in the list format required by the Process API."""
    return ["test", "command"]


@pytest.fixture
def encryption_key_file() -> Path:
    """Return an encryption key file path."""
    return Path("path", "to", "file.key")


@pytest.fixture
def encrypted_key_file() -> Path:
    """Return an encrypted encryption key path."""
    return Path("path", "to", "encryption.key.gpg")


@pytest.fixture
def spring_file_path() -> Path:
    """Return a spring file path."""
    return Path("path", "to", "file.spring")


@pytest.fixture
def encrypted_spring_file_path() -> Path:
    """Return an encrypted spring file Path object"""
    return Path("path", "to", "file.spring.gpg")


@pytest.fixture
def asymmetric_encryption_command(output_file_path: Path, input_file_path: Path) -> list[str]:
    """Return asymmetric encryption command."""
    return [
        "--encrypt",
        "--yes",
        "--recipient",
        EncryptionUserID.HASTA_USER_ID,
        "-o",
        output_file_path.as_posix(),
        input_file_path.as_posix(),
    ]


@pytest.fixture
def asymmetric_decryption_command(output_file_path: Path, input_file_path: Path) -> list[str]:
    """Return asymmetric decryption command."""
    return [
        "--decrypt",
        "--yes",
        "--batch",
        "--cipher-algo",
        CipherAlgorithm.AES256,
        "--passphrase",
        EncryptionUserID.HASTA_USER_ID,
        "-o",
        output_file_path.as_posix(),
        input_file_path.as_posix(),
    ]


@pytest.fixture
def symmetric_encryption_command(
    temporary_passphrase: Path,
    input_file_path: Path,
    output_file_path: Path,
    spring_file_path: Path,
) -> list[str]:
    """Return symmetric encryption command."""
    return [
        "--symmetric",
        "--yes",
        "--cipher-algo",
        CipherAlgorithm.AES256,
        "--batch",
        "--compress-algo",
        "None",
        "--passphrase-file",
        temporary_passphrase.as_posix(),
        "-o",
        output_file_path.as_posix(),
        input_file_path.as_posix(),
    ]


@pytest.fixture
def symmetric_decryption_command(
    encryption_key_file: Path,
    input_file_path: Path,
    output_file_path: Path,
) -> list:
    """Return symmetric decryption command."""
    return [
        "--decrypt",
        "--yes",
        "--cipher-algo",
        CipherAlgorithm.AES256,
        "--batch",
        "--passphrase-file",
        encryption_key_file.as_posix(),
        "-o",
        output_file_path.as_posix(),
        input_file_path.as_posix(),
    ]


@pytest.fixture
def spring_symmetric_encryption_command(
    temporary_passphrase: Path, encrypted_spring_file_path: Path, spring_file_path: Path
) -> list[str]:
    """Return symmetric encryption command."""
    return [
        "--symmetric",
        "--yes",
        "--cipher-algo",
        CipherAlgorithm.AES256,
        "--batch",
        "--compress-algo",
        "None",
        "--passphrase-file",
        temporary_passphrase.as_posix(),
        "-o",
        encrypted_spring_file_path.as_posix(),
        spring_file_path.as_posix(),
    ]


@pytest.fixture
def key_asymmetric_encryption_command(
    encrypted_key_file: Path, temporary_passphrase: Path
) -> list[str]:
    """Return asymmetric encryption command."""
    return [
        "--encrypt",
        "--yes",
        "--recipient",
        EncryptionUserID.HASTA_USER_ID,
        "-o",
        encrypted_key_file.as_posix(),
        temporary_passphrase.as_posix(),
    ]


@pytest.fixture
def spring_symmetric_decryption_command(
    encryption_key_file: Path,
    spring_file_path: Path,
    encrypted_spring_file_path,
) -> list[str]:
    """Return symmetric decryption_command."""
    return [
        "--decrypt",
        "--yes",
        "--cipher-algo",
        CipherAlgorithm.AES256,
        "--batch",
        "--passphrase-file",
        encryption_key_file.as_posix(),
        "-o",
        spring_file_path.as_posix(),
        encrypted_spring_file_path.as_posix(),
    ]


@pytest.fixture
def key_asymmetric_decryption_command(
    encrypted_key_file: Path, encryption_key_file: Path
) -> list[str]:
    """Return asymmetric encryption command."""
    return [
        "--decrypt",
        "--yes",
        "--batch",
        "--cipher-algo",
        CipherAlgorithm.AES256,
        "--passphrase",
        EncryptionUserID.HASTA_USER_ID,
        "-o",
        encryption_key_file.as_posix(),
        encrypted_key_file.as_posix(),
    ]
