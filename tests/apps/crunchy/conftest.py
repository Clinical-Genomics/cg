"""Fixtures for crunchy api"""
import copy
import json
import logging
from pathlib import Path
from typing import List

import pytest

from cg.apps.crunchy.models import CrunchyFileSchema
from cg.models import CompressionData

LOG = logging.getLogger(__name__)


class MockProcess:
    """Mock a process"""

    def __init__(self, process_name: str):
        """Inititalise mock"""
        self.stderr = ""
        self.stdout = ""
        self.base_call = [process_name]
        self.process_name = process_name

    def run_command(self, parameters: List):
        """Mock the run process method"""
        command = copy.deepcopy(self.base_call)
        if parameters:
            command.extend(parameters)

        LOG.info("Running command %s", " ".join(command))


# File fixtures


@pytest.fixture(scope="function", name="run_name")
def fixture_run_name() -> str:
    """Return the name of a fastq run"""
    return "fastq_run"


@pytest.fixture(scope="function", name="fastq_stub")
def fixture_fastq_stub(project_dir: Path, run_name: str) -> Path:
    """Creates a path to the base format of a fastq run"""
    return project_dir / run_name


@pytest.fixture(scope="function", name="compression_object")
def fixture_compression_object(fastq_stub: Path) -> CompressionData:
    """Creates compression data object with information about files used in fastq compression"""
    return CompressionData(fastq_stub)


@pytest.fixture(scope="function", name="file_schema")
def fixture_file_schema():
    """Return a instance of the file schema that describes content of spring metadata"""
    return CrunchyFileSchema()


@pytest.fixture(name="real_spring_metadata_path")
def fixture_real_spring_metadata_path(fixtures_dir):
    """Return the path to a spring metadata file"""
    return fixtures_dir / "apps" / "crunchy" / "spring_metadata.json"


@pytest.fixture(name="spring_metadata")
def fixture_spring_metadata(compression_object: CompressionData) -> List[dict]:
    """Return metada information"""
    first_read = compression_object.fastq_first
    second_read = compression_object.fastq_second
    spring_path = compression_object.spring_path
    metadata = [
        {
            "path": str(first_read),
            "file": "first_read",
            "checksum": "checksum_first_read",
            "algorithm": "sha256",
        },
        {
            "path": str(second_read),
            "file": "second_read",
            "checksum": "checksum_second_read",
            "algorithm": "sha256",
        },
        {"path": str(spring_path), "file": "spring"},
    ]
    return metadata


@pytest.fixture(scope="function", name="spring_metadata_file")
def fixture_spring_metadata_file(
    compression_object: CompressionData, spring_metadata: List[dict]
) -> Path:
    """Return the path to a populated spring metadata file"""
    metadata_path = compression_object.spring_metadata_path

    with open(metadata_path, "w") as outfile:
        outfile.write(json.dumps(spring_metadata))

    return metadata_path


@pytest.fixture(scope="function", name="sbatch_process")
def fixture_sbatch_process():
    """Return a mocked process object"""
    return MockProcess("sbatch")


@pytest.fixture(scope="function", name="fastq_first_file")
def fixture_fastq_first_file(fastq_first_path):
    """Creates an existing FASTQ path"""
    fastq_first_path.touch()
    return fastq_first_path


@pytest.fixture(scope="function", name="fastq_second_file")
def fixture_fastq_second_file(fastq_second_path):
    """Creates an existing FASTQ path"""
    fastq_second_path.touch()
    return fastq_second_path


@pytest.fixture(scope="function", name="spring_file")
def fixture_spring_file(spring_path):
    """Creates an existing SPRING file"""
    spring_path.touch()
    return spring_path


@pytest.fixture(scope="function", name="fastq_paths")
def fixture_fastq_paths(fastq_first_path, fastq_second_path):
    """Creates fastq paths"""
    return {
        "fastq_first_path": fastq_first_path,
        "fastq_second_path": fastq_second_path,
    }


@pytest.fixture(scope="function", name="existing_fastq_paths")
def fixture_existing_fastq_paths(fastq_first_file, fastq_second_file):
    """Creates existing FASTQ paths"""
    return {
        "fastq_first_path": fastq_first_file,
        "fastq_second_path": fastq_second_file,
    }


@pytest.fixture(scope="function", name="compressed_fastqs")
def fixture_compressed_fastqs(existing_fastq_paths, spring_file, spring_metadata_file):
    """Creates fastqs with corresponding SPRING and FLAG"""
    fastq_paths = existing_fastq_paths
    flag_path = spring_metadata_file

    assert spring_file.exists()
    assert flag_path.exists()
    return fastq_paths


@pytest.fixture(scope="function", name="compressed_fastqs_without_spring")
def fixture_compressed_fastqs_without_spring(existing_fastq_paths):
    """Creates fastqs with corresponding FLAG"""
    fastq_paths = existing_fastq_paths
    flag_path = Path(
        str(fastq_paths["fastq_first_path"]).replace(FASTQ_FIRST_READ_SUFFIX, ".crunchy.txt")
    )
    flag_path.touch()
    assert flag_path.exists()
    return fastq_paths


@pytest.fixture(scope="function", name="compressed_fastqs_without_flag")
def fixture_compressed_fastqs_without_flag(existing_fastq_paths, spring_file):
    """Creates fastqs with corresponding SPRING"""
    fastq_paths = existing_fastq_paths
    assert spring_file.exists()
    return fastq_paths


@pytest.fixture(scope="function", name="compressed_fastqs_pending")
def fixture_compressed_fastqs_pending(existing_fastq_paths):
    """Creates fastqs with corresponding PENDING"""
    fastq_paths = existing_fastq_paths
    pending_path = Path(
        str(fastq_paths["fastq_first_path"]).replace(
            FASTQ_FIRST_READ_SUFFIX, ".crunchy.pending.txt"
        )
    )
    pending_path.touch()
    assert pending_path.exists()
    return fastq_paths
