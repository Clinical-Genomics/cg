"""Fixtures for compress api tests"""
import copy
import json
import os
from pathlib import Path
from datetime import datetime

import pytest

from cg.apps.crunchy import CrunchyAPI
from cg.meta.compress import CompressAPI


class CompressionData:
    """Class to hold some data files"""

    def __init__(self, **kwargs):
        self.spring_path = kwargs["spring_path"]
        self.pending_path = kwargs["pending_path"]
        self.spring_metadata_path = kwargs["spring_metadata_path"]
        self.fastq_first = kwargs["fastq_first"]
        self.fastq_second = kwargs["fastq_second"]

    @property
    def spring_file(self):
        """Return the path to an existing spring file"""
        self.spring_path.touch()
        return self.spring_path

    @property
    def pending_file(self):
        """Return the path to an existing pending file"""
        self.pending_path.touch()
        return self.pending_path

    @staticmethod
    def _spring_metadata(fastq_first, fastq_second, spring_path, updated=False, date=None):
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
        if updated:
            for file_info in metadata:
                file_info["updated"] = date or "2020-01-21"
        return metadata

    @property
    def spring_metadata_file(self):
        """Return the path to an existing spring metadata file"""

        spring_metadata = CompressionData._spring_metadata(
            self.fastq_first, self.fastq_second, self.spring_path
        )
        with open(self.spring_metadata_path, "w") as outfile:
            outfile.write(json.dumps(spring_metadata))

        return self.spring_metadata_path

    @property
    def updated_spring_metadata_file(self):
        """Return the path to an existing spring metadata file"""

        spring_metadata = CompressionData._spring_metadata(
            self.fastq_first, self.fastq_second, self.spring_path, True
        )
        with open(self.spring_metadata_path, "w") as outfile:
            outfile.write(json.dumps(spring_metadata))

        return self.spring_metadata_path

    @staticmethod
    def make_old(file_path):
        """"Convert the modifying date so that the file looks old"""
        # Convert the date to a float
        before_timestamp = datetime.timestamp(datetime(2020, 1, 1))
        # Update the utime so file looks old
        os.utime(file_path, (before_timestamp, before_timestamp))

    @property
    def fastq_first_file(self, old: bool = True):
        """Return the path to an existing spring metadata file"""
        self.fastq_first.touch()
        if old:
            CompressionData.make_old(self.fastq_first)
        return self.fastq_first

    @property
    def fastq_second_file(self, old: bool = True):
        """Return the path to an existing fastq file"""
        self.fastq_second.touch()
        if old:
            CompressionData.make_old(self.fastq_second)
        return self.fastq_second


@pytest.yield_fixture(scope="function", name="compression_files")
def fixture_compression_files(compression_object):
    """Return a small class with compression files"""
    return CompressionData(
        spring_path=compression_object.spring_path,
        spring_metadata_path=compression_object.spring_metadata_path,
        fastq_first=compression_object.fastq_first,
        fastq_second=compression_object.fastq_second,
        pending_path=compression_object.pending_path,
    )


@pytest.yield_fixture(scope="function", name="real_crunchy_api")
def fixture_real_crunchy_api(crunchy_config_dict):
    """crunchy api fixture"""

    yield CrunchyAPI(crunchy_config_dict)


@pytest.yield_fixture(scope="function", name="compress_api")
def fixture_compress_api(real_crunchy_api, housekeeper_api):
    """compress api fixture"""
    hk_api = housekeeper_api
    _api = CompressAPI(crunchy_api=real_crunchy_api, hk_api=hk_api)
    yield _api


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


@pytest.fixture(scope="function", name="spring_path")
def fixture_spring_path(compression_object) -> Path:
    """Return the path to a non existing spring file"""
    return compression_object.spring_path


@pytest.fixture(scope="function", name="spring_metadata_path")
def fixture_spring_metadata_path(compression_object) -> Path:
    """Return the path to a non existing spring metadata file"""
    return compression_object.spring_metadata_path


@pytest.fixture(scope="function", name="fastq_flag_path")
def fixture_fastq_flag_path(spring_metadata_path) -> Path:
    """Return the path to a non existing fastq flag file"""
    return spring_metadata_path


@pytest.fixture(scope="function", name="fastq_flag_file")
def fixture_fastq_flag_file(spring_metadata_path) -> Path:
    """Return the path to an existing fastq flag file"""
    spring_metadata_path.touch()
    return spring_metadata_path


@pytest.fixture(scope="function", name="spring_file")
def fixture_spring_file(spring_path) -> Path:
    """Return the path to an existing spring file"""
    spring_path.touch()
    return spring_path


@pytest.fixture(scope="function", name="multi_linked_file")
def fixture_multi_linked_file(spring_path, project_dir) -> Path:
    """Return the path to an existing file with two links"""
    first_link = project_dir / "link-1"
    os.link(spring_path, first_link)

    return spring_path


@pytest.fixture(scope="function", name="fastq_paths")
def fixture_fastq_paths(compression_object):
    """Fixture for temporary fastq-files

    Create fastq paths and return a dictionary with them
    """
    return {
        "fastq_first_path": compression_object.fastq_first,
        "fastq_second_path": compression_object.fastq_second,
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


@pytest.fixture(scope="function", name="decompress_hk_spring_bundle")
def fixture_decompress_hk_spring_bundle(
    sample_hk_bundle_no_files, spring_file, fastq_flag_file, sample
):
    """Create a complete bundle mock for testing decompression

    This bundle contains a spring file and a spring metadata file
    """
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
