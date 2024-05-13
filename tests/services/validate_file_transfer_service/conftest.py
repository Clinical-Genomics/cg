from pathlib import Path

import pytest

from cg.services.validate_file_transfer_service.validate_file_transfer_service import (
    ValidateFileTransferService,
)


@pytest.fixture
def manifest_file(fixtures_dir: Path) -> Path:
    """Return the path to a manifest file."""
    return Path(fixtures_dir, "services", "validate_file_transfer_service", "pacbio_transfer_done")


@pytest.fixture
def manifest_file_fail(fixtures_dir: Path) -> Path:
    """Return the path to a manifest file."""
    return Path(
        fixtures_dir, "services", "validate_file_transfer_service", "pacbio_transfer_done_fail"
    )


@pytest.fixture
def source_dir(tmp_path: Path) -> Path:
    """Return the path to a source directory with files in different directories."""
    tmp_path.mkdir(exist_ok=True)
    tmp_path.joinpath("tree_1").mkdir()
    tmp_path.joinpath("tree_1/tree2").mkdir()
    tmp_path.joinpath("tree_1/tree2/tree3").mkdir()
    tmp_path.joinpath("file1").touch()
    tmp_path.joinpath("tree_1/file2").touch()
    tmp_path.joinpath("tree_1/file3").touch()
    tmp_path.joinpath("tree_1/tree2/file4").touch()
    tmp_path.joinpath("tree_1/tree2/tree3/file5").touch()
    return tmp_path


@pytest.fixture
def validate_file_transfer_service() -> ValidateFileTransferService:
    """Return the validate file transfer service."""
    return ValidateFileTransferService()


@pytest.fixture
def expected_file_names_in_manifest() -> list[str]:
    file_names: list[str] = []
    for i in range(1, 6):
        file_names.append(f"file{i}")
    return file_names
