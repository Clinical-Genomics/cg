"""Fixtures for crunchy api"""
import logging
from pathlib import Path
from typing import List

import pytest

from cg.constants.constants import FileFormat
from cg.io.controller import WriteFile
from cg.models import CompressionData
from cgmodels.crunchy.metadata import CrunchyMetadata
from tests.mocks.process_mock import ProcessMock

LOG = logging.getLogger(__name__)


@pytest.fixture(name="real_spring_metadata_path")
def fixture_real_spring_metadata_path(apps_dir: Path) -> Path:
    """Return the path to a SPRING metadata file"""
    return Path(apps_dir, "crunchy", "spring_metadata.json")


@pytest.fixture(name="spring_metadata")
def fixture_spring_metadata(compression_object: CompressionData) -> List[dict]:
    """Return meta data information"""
    return [
        {
            "path": compression_object.fastq_first.as_posix(),
            "file": "first_read",
            "checksum": "checksum_first_read",
            "algorithm": "sha256",
        },
        {
            "path": compression_object.fastq_second.as_posix(),
            "file": "second_read",
            "checksum": "checksum_second_read",
            "algorithm": "sha256",
        },
        {"path": compression_object.spring_path.as_posix(), "file": "spring"},
    ]


@pytest.fixture(name="crunchy_metadata_object")
def fixture_crunchy_metadata_object(spring_metadata: List[dict]) -> CrunchyMetadata:
    """Return the parsed metadata"""
    return CrunchyMetadata(files=spring_metadata)


@pytest.fixture(name="spring_metadata_file")
def fixture_spring_metadata_file(
    compression_object: CompressionData, spring_metadata: List[dict]
) -> Path:
    """Return the path to a populated SPRING metadata file"""
    metadata_path = compression_object.spring_metadata_path

    WriteFile.write_file_from_content(
        content=spring_metadata, file_format=FileFormat.JSON, file_path=metadata_path
    )
    return metadata_path


@pytest.fixture(scope="function", name="sbatch_process")
def fixture_sbatch_process(sbatch_job_number: int) -> ProcessMock:
    """Return a mocked process object"""
    slurm_process = ProcessMock(binary="sbatch")
    slurm_process.set_stdout(text=str(sbatch_job_number))
    return slurm_process


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
    """Creates FASTQ paths"""
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
    """Creates FASTQs with corresponding SPRING and FLAG"""
    fastq_paths = existing_fastq_paths
    flag_path = spring_metadata_file

    assert spring_file.exists()
    assert flag_path.exists()
    return fastq_paths
