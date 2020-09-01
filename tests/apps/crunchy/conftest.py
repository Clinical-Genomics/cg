"""Fixtures for crunchy api"""
import copy
import json
import logging
from pathlib import Path
from typing import List

import pytest

from cg.apps.crunchy import CrunchyAPI
from cg.apps.crunchy.models import CrunchyFileSchema
from cg.constants import FASTQ_FIRST_READ_SUFFIX, FASTQ_SECOND_READ_SUFFIX

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


@pytest.fixture(scope="function", name="file_schema")
def fixture_file_schema():
    """Return a instance of the file schema that describes content of spring metadata"""
    return CrunchyFileSchema()


@pytest.fixture(name="real_spring_metadata_path")
def fixture_real_spring_metadata_path(fixtures_dir):
    """Return the path to a spring metadata file"""
    return fixtures_dir / "apps" / "crunchy" / "spring_metadata.json"


@pytest.fixture(name="spring_metadata")
def fixture_spring_metadata(fastq_paths, spring_path):
    """Return metada information"""
    first_read = fastq_paths["fastq_first_path"]
    second_read = fastq_paths["fastq_second_path"]
    metadata = [
        {
            "path": str(first_read.resolve()),
            "file": "first_read",
            "checksum": "checksum_first_read",
            "algorithm": "sha256",
        },
        {
            "path": str(second_read.resolve()),
            "file": "second_read",
            "checksum": "checksum_second_read",
            "algorithm": "sha256",
        },
        {"path": str(spring_path.resolve()), "file": "spring"},
    ]
    return metadata


@pytest.fixture(scope="function", name="spring_metadata_file")
def fixture_spring_metadata_file(spring_path, spring_metadata):
    """Return the path to a populated spring metadata file"""
    metadata_path = CrunchyAPI.get_flag_path(spring_path)
    print("spring_path", spring_path)
    with open(metadata_path, "w") as outfile:
        outfile.write(json.dumps(spring_metadata))

    with open(metadata_path, "r") as outfile:
        print(json.loads(outfile.read()))

    return metadata_path


@pytest.fixture(scope="function", name="sbatch_process")
def fixture_sbatch_process():
    """Return a mocked process object"""
    return MockProcess("sbatch")


@pytest.fixture(scope="function", name="bam_path")
def fixture_bam_path(project_dir):
    """Creates a BAM path"""
    _bam_path = project_dir / "file.bam"
    return _bam_path


@pytest.fixture(scope="function", name="fastq_first_path")
def fixture_fastq_first_path(project_dir):
    """Creates a FASTQ path to first read in pair"""
    _path = project_dir / ("file" + FASTQ_FIRST_READ_SUFFIX)
    return _path


@pytest.fixture(scope="function", name="fastq_second_path")
def fixture_fastq_second_path(project_dir):
    """Creates a FASTQ path to second read in pair"""
    _path = project_dir / ("file" + FASTQ_SECOND_READ_SUFFIX)
    return _path


@pytest.fixture(scope="function", name="spring_path")
def fixture_spring_path(fastq_first_path):
    """Creates a SPRING path"""
    _path = CrunchyAPI.get_spring_path_from_fastq(fastq_first_path)
    return _path


@pytest.fixture(scope="function", name="existing_bam_path")
def fixture_existing_bam_path(bam_path):
    """Creates an existing BAM path"""
    bam_path.touch()
    return bam_path


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


@pytest.fixture(scope="function", name="compressed_bam")
def fixture_compressed_bam(existing_bam_path):
    """Creates BAM with corresponding CRAM, CRAI and FLAG"""
    bam_path = existing_bam_path
    cram_path = bam_path.with_suffix(".cram")
    crai_path = bam_path.with_suffix(".cram.crai")
    flag_path = bam_path.with_suffix(".crunchy.txt")
    cram_path.touch()
    crai_path.touch()
    flag_path.touch()
    assert bam_path.exists()
    assert cram_path.exists()
    assert crai_path.exists()
    assert flag_path.exists()
    return bam_path


@pytest.fixture(scope="function", name="compressed_bam_without_crai")
def fixture_compressed_bam_without_crai(existing_bam_path):
    """Creates BAM with corresponding CRAM and FLAG, but no CRAI"""
    bam_path = existing_bam_path
    cram_path = bam_path.with_suffix(".cram")
    flag_path = bam_path.with_suffix(".crunchy.txt")
    cram_path.touch()
    flag_path.touch()
    assert bam_path.exists()
    assert cram_path.exists()
    assert flag_path.exists()
    return bam_path


@pytest.fixture(scope="function", name="compressed_bam_without_flag")
def fixture_compressed_bam_without_flag(existing_bam_path):
    """Creates BAM with corresponding CRAM and FLAG, but no CRAI"""
    bam_path = existing_bam_path
    cram_path = bam_path.with_suffix(".cram")
    crai_path = bam_path.with_suffix(".cram.crai")
    cram_path.touch()
    crai_path.touch()
    assert bam_path.exists()
    assert cram_path.exists()
    assert crai_path.exists()
    return bam_path


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


@pytest.fixture(scope="function")
def mock_bam_to_cram():
    """This fixture returns a mocked bam_to_cram method. this mock_method
    Will create files with suffixes .cram and .crai for a given BAM path"""

    def _mock_bam_to_cram_func(bam_path: Path, dry_run: bool = False):

        _ = dry_run

        cram_path = bam_path.with_suffix(".cram")
        crai_path = bam_path.with_suffix(".cram.crai")
        flag_path = bam_path.with_suffix(".crunchy.txt")

        cram_path.touch()
        crai_path.touch()
        flag_path.touch()

    return _mock_bam_to_cram_func
