"""Fixtures for Compress API tests."""
import copy
from typing import List, Dict, Any, Generator

import os
from datetime import datetime
from pathlib import Path

import pytest

from cg.apps.crunchy import CrunchyAPI
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import SequencingFileTag
from cg.constants.constants import FileFormat
from cg.io.controller import WriteFile
from cg.meta.compress import CompressAPI
from tests.cli.compress.conftest import MockCompressAPI
from tests.store_helpers import StoreHelpers


class MockCompressionData:
    """Class to hold compression files."""

    def __init__(self, **kwargs):
        self.spring_path: Path = kwargs["spring_path"]
        self.pending_path: Path = kwargs["pending_path"]
        self.spring_metadata_path: Path = kwargs["spring_metadata_path"]
        self.fastq_first: Path = kwargs["fastq_first"]
        self.fastq_second: Path = kwargs["fastq_second"]

    @property
    def spring_file(self) -> Path:
        """Return the path to an existing SPRING file."""
        self.spring_path.touch()
        return self.spring_path

    @property
    def pending_file(self) -> Path:
        """Return the path to an existing SPRING pending file."""
        self.pending_path.touch()
        return self.pending_path

    @staticmethod
    def _spring_metadata(
        fastq_first: Path,
        fastq_second: Path,
        spring_path: Path,
        updated: bool = False,
        date: datetime = None,
    ) -> List[dict]:
        """Return SPRING metadata."""
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
    def spring_metadata_file(self) -> Path:
        """Return the path to an existing SPRING metadata file."""

        spring_metadata: List[dict] = MockCompressionData._spring_metadata(
            self.fastq_first, self.fastq_second, self.spring_path
        )
        WriteFile.write_file_from_content(
            content=spring_metadata,
            file_format=FileFormat.JSON,
            file_path=self.spring_metadata_path,
        )
        return self.spring_metadata_path

    @property
    def updated_spring_metadata_file(self) -> Path:
        """Return the path to an existing updated SPRING metadata file."""
        spring_metadata: List[dict] = MockCompressionData._spring_metadata(
            self.fastq_first, self.fastq_second, self.spring_path, True
        )
        WriteFile.write_file_from_content(
            content=spring_metadata,
            file_format=FileFormat.JSON,
            file_path=self.spring_metadata_path,
        )
        return self.spring_metadata_path

    @staticmethod
    def make_old(file_path: Path):
        """Convert the modifying date making the file old."""
        before_timestamp = datetime.timestamp(datetime(2020, 1, 1))
        os.utime(file_path, (before_timestamp, before_timestamp))

    @property
    def fastq_first_file(self, old: bool = True) -> Path:
        """Return the path to an existing first read FASTQ file."""
        self.fastq_first.touch()
        if old:
            MockCompressionData.make_old(self.fastq_first)
        return self.fastq_first

    @property
    def fastq_second_file(self, old: bool = True) -> Path:
        """Return the path to an existing second read FASTQ file."""
        self.fastq_second.touch()
        if old:
            MockCompressionData.make_old(self.fastq_second)
        return self.fastq_second


@pytest.fixture(name="compression_files")
def fixture_compression_files(compression_object: MockCompressionData) -> MockCompressionData:
    """Return a CompressionData class with files."""
    return MockCompressionData(
        spring_path=compression_object.spring_path,
        spring_metadata_path=compression_object.spring_metadata_path,
        fastq_first=compression_object.fastq_first,
        fastq_second=compression_object.fastq_second,
        pending_path=compression_object.pending_path,
    )


@pytest.fixture(name="real_crunchy_api")
def fixture_real_crunchy_api(
    crunchy_config: Dict[str, Dict[str, Any]]
) -> Generator[CrunchyAPI, None, None]:
    """Crunchy API fixture."""
    yield CrunchyAPI(crunchy_config)


@pytest.fixture(name="compress_api")
def fixture_compress_api(
    demultiplexed_runs: Path,
    real_crunchy_api: CrunchyAPI,
    housekeeper_api: HousekeeperAPI,
    project_dir: Path,
) -> Generator[CompressAPI, None, None]:
    """Return Compress API."""
    yield CompressAPI(
        crunchy_api=real_crunchy_api, hk_api=housekeeper_api, demux_root=project_dir.as_posix()
    )


@pytest.fixture(name="populated_compress_fastq_api")
def fixture_populated_compress_fastq_api(
    compress_api: MockCompressAPI, compress_hk_fastq_bundle: dict, helpers: StoreHelpers
) -> MockCompressAPI:
    """Return populated Compress API."""
    helpers.ensure_hk_bundle(compress_api.hk_api, compress_hk_fastq_bundle)
    return compress_api


@pytest.fixture(name="populated_decompress_spring_api")
def fixture_populated_decompress_spring_api(
    compress_api: MockCompressAPI, decompress_hk_spring_bundle: dict, helpers: StoreHelpers
) -> MockCompressAPI:
    """Return populated Compress API with a Housekeeper bundle containing SPRING files."""
    helpers.ensure_hk_bundle(compress_api.hk_api, decompress_hk_spring_bundle)
    return compress_api


@pytest.fixture(name="sample")
def fixture_sample():
    """Return the sample id for first sample."""
    return "sample_1"


@pytest.fixture(name="spring_path")
def fixture_spring_path(compression_object: MockCompressionData) -> Path:
    """Return the path to a non-existing spring file."""
    return compression_object.spring_path


@pytest.fixture(name="spring_metadata_path")
def fixture_spring_metadata_path(compression_object: MockCompressionData) -> Path:
    """Return the path to a non-existing spring metadata file."""
    return compression_object.spring_metadata_path


@pytest.fixture(name="fastq_flag_path")
def fixture_fastq_flag_path(spring_metadata_path: Path) -> Path:
    """Return the path to a non-existing fastq flag file."""
    return spring_metadata_path


@pytest.fixture(name="fastq_flag_file")
def fixture_fastq_flag_file(spring_metadata_path: Path) -> Path:
    """Return the path to an existing fastq flag file."""
    spring_metadata_path.touch()
    return spring_metadata_path


@pytest.fixture(name="spring_file")
def fixture_spring_file(spring_path: Path) -> Path:
    """Return the path to an existing spring file."""
    spring_path.touch()
    return spring_path


@pytest.fixture(name="multi_linked_file")
def fixture_multi_linked_file(spring_path: Path, project_dir: Path) -> Path:
    """Return the path to an existing file with two links."""
    first_link = Path(project_dir, "link-1")
    os.link(spring_path, first_link)
    return spring_path


@pytest.fixture(name="fastq_paths")
def fixture_fastq_paths(compression_object: MockCompressionData) -> Dict[str, Path]:
    """Return temporary fastq-files."""
    return {
        "fastq_first_path": compression_object.fastq_first,
        "fastq_second_path": compression_object.fastq_second,
    }


@pytest.fixture(name="fastq_files")
def fixture_fastq_files(fastq_paths: Dict[str, Path]) -> Dict[str, Path]:
    """Return temporary fastq-files that exist."""
    fastq_first_file: Path = fastq_paths["fastq_first_path"]
    fastq_second_file: Path = fastq_paths["fastq_second_path"]
    fastq_first_file.touch()
    fastq_second_file.touch()
    return fastq_paths


# Bundle fixtures


@pytest.fixture(name="decompress_hk_spring_bundle")
def fixture_decompress_hk_spring_bundle(
    sample_hk_bundle_no_files: dict, spring_file: Path, fastq_flag_file: Path, sample: str
) -> dict:
    """Create a complete bundle mock for testing decompression.

    This bundle contains a spring file and a spring metadata file.
    """
    hk_spring_bundle: dict = copy.deepcopy(sample_hk_bundle_no_files)

    spring_file_info: dict = {
        "path": spring_file.as_posix(),
        "archive": False,
        "tags": [sample, SequencingFileTag.SPRING],
    }
    spring_meta_info: dict = {
        "path": fastq_flag_file.as_posix(),
        "archive": False,
        "tags": [sample, SequencingFileTag.SPRING_METADATA],
    }

    hk_spring_bundle["files"].extend([spring_file_info, spring_meta_info])
    return hk_spring_bundle
