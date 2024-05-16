from pathlib import Path

import pytest

from cg.models.cg_config import CGConfig
from cg.services.validate_file_transfer_service.validate_file_transfer_service import (
    ValidateFileTransferService,
)
from cg.services.validate_file_transfer_service.validate_pacbio_file_transfer_service import (
    ValidatePacbioFileTransferService,
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
def transfer_source_dir(tmp_path: Path) -> Path:
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


@pytest.fixture
def pacbio_run_id() -> str:
    """Return a PacBio run ID."""
    return "r1123_221421_12321"


@pytest.fixture
def smrt_cell_id() -> str:
    """Return a PacBio smrt cell ID."""
    return "1_A1_0"


@pytest.fixture
def metadata_dir_name() -> str:
    """Return a metadata directory name."""
    return "metadata"


@pytest.fixture
def tmp_manifest_file_name(pacbio_run_id: str, smrt_cell_id: str) -> str:
    """Return a temporary manifest file name."""
    return f"{pacbio_run_id}_{smrt_cell_id}.transferdone"


@pytest.fixture
def pacbio_runs_dir(
    tmp_path: Path, pacbio_run_id: str, smrt_cell_id, metadata_dir_name: str, tmp_manifest_file_name
) -> Path:
    """Return the path to a directory with PacBio runs."""
    tmp_path.mkdir(exist_ok=True)
    tmp_path.joinpath(pacbio_run_id).mkdir()
    tmp_path.joinpath(pacbio_run_id).joinpath(smrt_cell_id).mkdir()
    tmp_path.joinpath(pacbio_run_id).joinpath(smrt_cell_id).joinpath(metadata_dir_name).mkdir()
    tmp_path.joinpath(pacbio_run_id).joinpath(smrt_cell_id).joinpath(metadata_dir_name).joinpath(
        tmp_manifest_file_name
    ).touch()
    tmp_path.joinpath("not_this_dir").mkdir()
    return tmp_path


@pytest.fixture
def validate_pacbio_service(
    cg_context: CGConfig, pacbio_runs_dir: Path
) -> ValidatePacbioFileTransferService:
    """Return a PacBio file transfer service."""
    validate_pacbio_file_transfer_service = ValidatePacbioFileTransferService(config=cg_context)
    validate_pacbio_file_transfer_service.data_dir = pacbio_runs_dir.as_posix()
    validate_pacbio_file_transfer_service.trigger_dir = pacbio_runs_dir.as_posix()
    return validate_pacbio_file_transfer_service
