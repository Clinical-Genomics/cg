"""Fixtures for compress api tests"""
import copy
import json
import os
from pathlib import Path

import pytest

from cg.apps.crunchy import CrunchyAPI
from cg.constants import FASTQ_FIRST_READ_SUFFIX, FASTQ_SECOND_READ_SUFFIX
from cg.meta.compress import CompressAPI
from tests.mocks.hk_mock import MockFile


class CompressionData:
    """Class to hold some data files"""

    def __init__(self, **kwargs):
        self.spring_path = kwargs["spring_path"]
        self.spring_metadata_path = kwargs["spring_metadata_path"]
        self.fastq_first = kwargs["fastq_first"]
        self.fastq_second = kwargs["fastq_second"]

    @property
    def spring_file(self):
        """Return the path to an existing spring file"""
        self.spring_path.touch()
        return self.spring_path

    @property
    def spring_metadata_file(self):
        """Return the path to an existing spring metadata file"""

        def _spring_metadata(fastq_first, fastq_second, spring_path):
            """Return metada information"""
            metadata = [
                {
                    "path": str(fastq_first.resolve()),
                    "file": "first_read",
                    "checksum": "checksum_first_read",
                    "algorithm": "sha256",
                },
                {
                    "path": str(fastq_second.resolve()),
                    "file": "second_read",
                    "checksum": "checksum_second_read",
                    "algorithm": "sha256",
                },
                {"path": str(spring_path.resolve()), "file": "spring"},
            ]
            return metadata

        spring_metadata = _spring_metadata(self.fastq_first, self.fastq_second, self.spring_path)
        with open(self.spring_metadata_path, "w") as outfile:
            outfile.write(json.dumps(spring_metadata))

        return self.spring_metadata_path

    @property
    def fastq_first_file(self):
        """Return the path to an existing spring metadata file"""
        self.fastq_first.touch()
        return self.fastq_first

    @property
    def fastq_second_file(self):
        """Return the path to an existing fastq file"""
        self.fastq_second.touch()
        return self.fastq_second


@pytest.yield_fixture(scope="function", name="compression_files")
def fixture_compression_files(spring_path, spring_metadata_path, fastq_paths):
    """Return a small class with compression files"""
    return CompressionData(
        spring_path=spring_path,
        spring_metadata_path=spring_metadata_path,
        fastq_first=fastq_paths["fastq_first_path"],
        fastq_second=fastq_paths["fastq_second_path"],
    )


@pytest.yield_fixture(scope="function", name="real_crunchy_api")
def fixture_real_crunchy_api(crunchy_config_dict):
    """crunchy api fixture"""

    yield CrunchyAPI(crunchy_config_dict)


@pytest.yield_fixture(scope="function", name="compress_api")
def fixture_compress_api(crunchy_api, housekeeper_api):
    """compress api fixture"""
    hk_api = housekeeper_api
    _api = CompressAPI(crunchy_api=crunchy_api, hk_api=hk_api)
    yield _api


@pytest.fixture(scope="function", name="populated_compress_api")
def fixture_populated_compress_api(compress_api, compress_hk_bam_bundle, helpers):
    """Populated compress api fixture"""
    helpers.ensure_hk_bundle(compress_api.hk_api, compress_hk_bam_bundle)

    return compress_api


@pytest.fixture(scope="function", name="populated_compress_fastq_api")
def fixture_populated_compress_fastq_api(compress_api, compress_hk_fastq_bundle, helpers):
    """Populated compress api fixture"""
    helpers.ensure_hk_bundle(compress_api.hk_api, compress_hk_fastq_bundle)

    return compress_api


@pytest.fixture(scope="function", name="populated_decompress_spring_api")
def fixture_populated_decompress_spring_api(compress_api, decompress_hk_spring_bundle, helpers):
    """Populated compress api fixture"""
    helpers.ensure_hk_bundle(compress_api.hk_api, decompress_hk_spring_bundle)

    return compress_api


@pytest.fixture(scope="function", name="sample")
def fixture_sample():
    """Return the sample id for first sample"""
    return "sample_1"


@pytest.fixture(scope="function", name="sample_two")
def fixture_sample_two():
    """Return the sample id for second sample"""
    return "sample_2"


@pytest.fixture(scope="function", name="sample_three")
def fixture_sample_three():
    """Return the sample id for third sample"""
    return "sample_3"


@pytest.fixture(scope="function", name="sample_dir")
def fixture_sample_dir(project_dir, sample) -> Path:
    """Return the path to a sample directory"""
    _dir = project_dir / sample
    _dir.mkdir(parents=True, exist_ok=True)
    return _dir


@pytest.fixture(scope="function", name="spring_path")
def fixture_spring_path(fastq_paths) -> Path:
    """Return the path to a non existing spring file"""
    return CrunchyAPI.get_spring_path_from_fastq(fastq=fastq_paths["fastq_first_path"])


@pytest.fixture(scope="function", name="spring_metadata_path")
def fixture_spring_metadata_path(spring_path) -> Path:
    """Return the path to a non existing spring metadata file"""
    return CrunchyAPI.get_flag_path(file_path=spring_path)


@pytest.fixture(scope="function", name="fastq_flag_path")
def fixture_fastq_flag_path(spring_path) -> Path:
    """Return the path to a non existing fastq flag file"""
    return CrunchyAPI.get_flag_path(file_path=spring_path)


@pytest.fixture(scope="function", name="fastq_flag_file")
def fixture_fastq_flag_file(fastq_flag_path) -> Path:
    """Return the path to an existing fastq flag file"""
    fastq_flag_path.touch()
    return fastq_flag_path


@pytest.fixture(scope="function", name="spring_file")
def fixture_spring_file(spring_path) -> Path:
    """Return the path to an existing spring file"""
    spring_path.touch()
    return spring_path


@pytest.fixture(scope="function", name="multi_linked_file")
def fixture_multi_linked_file(bam_file, project_dir) -> Path:
    """Return the path to an existing file with two links"""
    first_link = project_dir / "link-1"
    os.link(bam_file, first_link)

    return bam_file


@pytest.fixture(scope="function", name="fastq_paths")
def fixture_fastq_paths(project_dir, sample):
    """Fixture for temporary fastq-files

    Create fastq paths and return a dictionary with them
    """
    sample_dir = project_dir / sample
    sample_dir.mkdir(parents=True, exist_ok=True)
    fastq_first_file = sample_dir / f"{sample}{FASTQ_FIRST_READ_SUFFIX}"
    fastq_second_file = sample_dir / f"{sample}{FASTQ_SECOND_READ_SUFFIX}"
    fastq_first_file.touch()
    fastq_second_file.touch()

    return {
        "fastq_first_path": fastq_first_file,
        "fastq_second_path": fastq_second_file,
    }


@pytest.fixture(scope="function", name="fastq_files")
def fixture_fastq_files(fastq_paths):
    """Fixture for temporary fastq-files

    Create fastq files and return a dictionary with them
    """
    fastq_first_file = fastq_paths["fastq_first_path"]
    fastq_second_file = fastq_paths["fastq_second_path"]
    fastq_first_file.touch()
    fastq_second_file.touch()

    return fastq_paths


# Bundle fixtures


@pytest.fixture(scope="function", name="sample_hk_bundle_no_files")
def fixture_sample_hk_bundle_no_files(sample, timestamp):
    """Create a complete bundle mock for testing compression"""
    hk_bundle_data = {
        "name": sample,
        "created": timestamp,
        "expires": timestamp,
        "files": [],
    }

    return hk_bundle_data


@pytest.fixture(scope="function", name="case_hk_bundle_no_files")
def fixture_case_hk_bundle_no_files(case_id, timestamp):
    """Create a complete bundle mock for testing compression"""
    hk_bundle_data = {
        "name": case_id,
        "created": timestamp,
        "expires": timestamp,
        "files": [],
    }

    return hk_bundle_data


@pytest.fixture(scope="function", name="compress_hk_fastq_bundle")
def fixture_compress_hk_fastq_bundle(fastq_files, sample_hk_bundle_no_files):
    """Create a complete bundle mock for testing compression"""
    hk_bundle_data = copy.deepcopy(sample_hk_bundle_no_files)

    first_fastq = fastq_files["fastq_first_path"]
    second_fastq = fastq_files["fastq_second_path"]
    for fastq_file in [first_fastq, second_fastq]:
        fastq_file_info = {"path": str(fastq_file), "archive": False, "tags": ["fastq"]}

        hk_bundle_data["files"].append(fastq_file_info)

    return hk_bundle_data


@pytest.fixture(scope="function", name="decompress_hk_spring_bundle")
def fixture_decompress_hk_spring_bundle(
    sample_hk_bundle_no_files, spring_file, fastq_flag_file, sample
):
    """Create a complete bundle mock for testing decompression"""
    hk_bundle_data = copy.deepcopy(sample_hk_bundle_no_files)

    spring_file_info = {"path": str(spring_file), "archive": False, "tags": [sample, "spring"]}
    spring_meta_info = {
        "path": str(fastq_flag_file),
        "archive": False,
        "tags": [sample, "spring-metadata"],
    }

    hk_bundle_data["files"].append(spring_file_info)
    hk_bundle_data["files"].append(spring_meta_info)

    return hk_bundle_data
