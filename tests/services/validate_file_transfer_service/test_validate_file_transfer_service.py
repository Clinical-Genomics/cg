"""Module to test the validate file transfer service."""

from pathlib import Path

from cg.constants.constants import FileFormat
from cg.services.validate_file_transfer_service.validate_file_transfer_service import (
    ValidateFileTransferService,
)


def test_get_manifest_content(
    validate_file_transfer_service: ValidateFileTransferService,
    manifest_file: Path,
):
    """Test the get manifest file content method."""
    # GIVEN a manifest file

    # WHEN getting the content of the manifest file
    manifest_content = validate_file_transfer_service.get_manifest_file_content(
        manifest_file=manifest_file, manifest_file_format=FileFormat.TXT
    )

    # THEN assert that the content is a list
    assert isinstance(manifest_content, list)


def test_get_file_names_from_content(
    validate_file_transfer_service: ValidateFileTransferService,
    manifest_file: Path,
    expected_file_names_in_manifest: list[str],
):
    """Test the get file names from content method."""
    # GIVEN a manifest file
    manifest_content = validate_file_transfer_service.get_manifest_file_content(
        manifest_file=manifest_file, manifest_file_format=FileFormat.TXT
    )

    # WHEN getting the file names from the content
    file_names = validate_file_transfer_service.extract_file_names_from_manifest(manifest_content)

    # THEN assert that the file names are a list
    assert isinstance(file_names, list)
    assert len(file_names) == len(expected_file_names_in_manifest)
    for file_name in file_names:
        assert file_name in expected_file_names_in_manifest


def test_is_file_in_directory(
    validate_file_transfer_service: ValidateFileTransferService,
    source_dir: Path,
    expected_file_names_in_manifest: list[str],
):
    """Test the is file in directory method."""
    # GIVEN a source directory and a list of file names
    for file_name in expected_file_names_in_manifest:
        # WHEN checking if the file is in the directory
        is_file_in_directory = validate_file_transfer_service.is_file_in_directory_tree(
            file_name=file_name, source_dir=source_dir
        )

        # THEN assert that the file is in the directory
        assert is_file_in_directory


def test_validate_by_manifest_file(
    validate_file_transfer_service: ValidateFileTransferService,
    manifest_file: Path,
    source_dir: Path,
):
    """Test the validate by manifest file method."""
    # GIVEN a manifest file and a source directory

    # WHEN validating the files in the manifest file
    is_valid = validate_file_transfer_service.validate_by_manifest_file(
        manifest_file=manifest_file, source_dir=source_dir, manifest_file_format=FileFormat.TXT
    )

    # THEN assert that the files in the manifest are in the directory
    assert is_valid


def test_validate_by_manifest_file_fail(
    validate_file_transfer_service: ValidateFileTransferService,
    manifest_file_fail: Path,
    source_dir: Path,
):
    """Test the validate by manifest file method."""
    # GIVEN a manifest file and a source directory

    # WHEN validating the files in the manifest file
    is_valid = validate_file_transfer_service.validate_by_manifest_file(
        manifest_file=manifest_file_fail, source_dir=source_dir, manifest_file_format=FileFormat.TXT
    )

    # THEN assert that the files in the manifest are not in the directory
    assert not is_valid