"""Tests for cleaning FASTQ files."""
import logging
from pathlib import Path
from typing import Generator, Dict, List

from _pytest.logging import LogCaptureFixture

from housekeeper.store.models import Version, File

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import SequencingFileTag
from cg.meta.compress import files
from cg.models import CompressionData
from tests.cli.compress.conftest import MockCompressAPI
from tests.meta.compress.conftest import MockCompressionData
from tests.store_helpers import StoreHelpers


def test_remove_fastqs(
    compress_api: MockCompressAPI,
    compression_object: MockCompressionData,
    caplog: LogCaptureFixture,
):
    """Test remove_fastq method."""
    caplog.set_level(logging.DEBUG)

    # GIVEN existing FASTQ and flag file
    fastq_first: Path = compression_object.fastq_first
    fastq_second: Path = compression_object.fastq_second
    fastq_first.touch()
    fastq_second.touch()
    compression_object.spring_metadata_path.touch()

    # WHEN calling remove_fastq
    compress_api.remove_fastq(fastq_first=fastq_first, fastq_second=fastq_second)

    # THEN assert that the FASTQ-files are deleted
    assert not fastq_first.exists()
    assert not fastq_second.exists()

    # THEN assert that the flag file is still there since this holds important information
    assert compression_object.spring_metadata_path.exists()
    expected_output: str = f"Will remove {fastq_first} and {fastq_second}"
    assert expected_output in caplog.text
    assert f"FASTQ file {fastq_first} removed" in caplog.text
    assert f"FASTQ file {fastq_second} removed" in caplog.text


def test_update_hk_fastq(
    root_path: Path,
    real_housekeeper_api: Generator[HousekeeperAPI, None, None],
    compress_hk_fastq_bundle: dict,
    compression_files: MockCompressionData,
    compress_api: MockCompressAPI,
    helpers: StoreHelpers,
):
    """Test to update the FASTQ and SPRING paths in Housekeeper after completed compression."""

    # GIVEN real Housekeeper API populated with a Housekeeper bundle
    sample_id: str = compress_hk_fastq_bundle["name"]
    hk_api: Generator[HousekeeperAPI, None, None] = real_housekeeper_api
    helpers.ensure_hk_bundle(hk_api, compress_hk_fastq_bundle)
    compress_api.hk_api = hk_api

    # GIVEN that there are FASTQ files in Housekeeper
    hk_fastq_files: list = list(hk_api.files(tags=[SequencingFileTag.FASTQ]))
    assert hk_fastq_files

    # GIVEN that the SPRING files exist in disk but has been not added to Housekeeper
    assert compression_files.spring_file.exists()
    assert compression_files.spring_metadata_file.exists()
    hk_spring_files: list = list(hk_api.files(tags=[SequencingFileTag.SPRING]))
    hk_spring_metadata_files: list = list(hk_api.files(tags=[SequencingFileTag.SPRING_METADATA]))
    for spring_file in [hk_spring_files, hk_spring_metadata_files]:
        assert not spring_file

    # GIVEN a Housekeeper version and a compression object
    hk_version: Version = compress_api.hk_api.get_latest_bundle_version(bundle_name=sample_id)
    fastq: Dict[str, dict] = files.get_fastq_files(sample_id=sample_id, version_obj=hk_version)
    run: str = list(fastq.keys())[0]
    compression: CompressionData = fastq[run]["compression_data"]

    # WHEN updating Housekeeper with compressed FASTQ files
    compress_api.update_fastq_hk(
        sample_id=sample_id,
        compression_obj=compression,
        hk_fastq_first=fastq[run]["hk_first"],
        hk_fastq_second=fastq[run]["hk_second"],
    )

    # THEN assert that the SPRING files have been added to Housekeeper
    hk_spring_files: List[File] = list(real_housekeeper_api.files(tags=[SequencingFileTag.SPRING]))
    hk_spring_metadata_files: List[File] = list(
        real_housekeeper_api.files(tags=[SequencingFileTag.SPRING_METADATA])
    )
    for spring_file in [hk_spring_files, hk_spring_metadata_files]:
        assert spring_file

    # THEN assert that the SPRING files have been added to bundles directory
    for spring_file in [hk_spring_files[0].path, hk_spring_metadata_files[0].path]:
        assert Path(root_path, spring_file).exists()

    # THEN assert that the FASTQ files are removed from Housekeeper
    hk_fastq_files: List[File] = list(hk_api.files(tags=[SequencingFileTag.FASTQ]))
    assert not hk_fastq_files


def test_cli_clean_fastqs_removed(
    populated_compress_fastq_api: MockCompressAPI,
    compression_files: MockCompressionData,
    sample: str,
):
    """Test to clean FASTQs after a successful FASTQ compression."""
    spring_file: Path = compression_files.spring_file
    spring_metadata_file: Path = compression_files.spring_metadata_file
    fastq_first: Path = compression_files.fastq_first_file
    fastq_second: Path = compression_files.fastq_second_file

    # GIVEN that the SPRING compression files exist
    assert spring_file.exists()
    assert spring_metadata_file.exists()

    # GIVEN that the FASTQ files exists
    assert fastq_first.exists()
    assert fastq_second.exists()

    # WHEN running the clean command
    populated_compress_fastq_api.clean_fastq(sample)

    # THEN assert SPRING files exists
    assert spring_file.exists()
    assert spring_metadata_file.exists()

    # THEN assert that the FASTQ files are removed
    assert not fastq_first.exists()
    assert not fastq_second.exists()


def test_cli_clean_fastqs_no_spring_metadata(
    populated_compress_fastq_api: MockCompressAPI,
    compression_files: MockCompressionData,
    sample: str,
):
    """Test to clean FASTQs when SPRING compression is not finished."""
    spring_file: Path = compression_files.spring_file
    spring_metadata_file: Path = compression_files.spring_metadata_path
    fastq_first: Path = compression_files.fastq_first_file
    fastq_second: Path = compression_files.fastq_second_file

    # GIVEN that the SPRING compression file exist
    assert spring_file.exists()

    # GIVEN that the SPRING metadata file does not exist
    assert not spring_metadata_file.exists()

    # WHEN running the clean command
    populated_compress_fastq_api.clean_fastq(sample)

    # THEN assert SPRING file exists
    assert spring_file.exists()

    # THEN assert that the FASTQ files are NOT removed
    assert fastq_first.exists()
    assert fastq_second.exists()


def test_cli_clean_fastqs_pending_compression_metadata(
    populated_compress_fastq_api: MockCompressAPI,
    compression_files: MockCompressionData,
    sample: str,
):
    """Test to clean FASTQs when SPRING compression is pending."""
    spring_file: Path = compression_files.spring_file
    fastq_first: Path = compression_files.fastq_first_file
    fastq_second: Path = compression_files.fastq_second_file

    # GIVEN that the SPRING compression file exist
    assert spring_file.exists()
    crunchy_flag_file = compression_files.pending_file
    assert crunchy_flag_file.exists()

    # WHEN running the clean command
    populated_compress_fastq_api.clean_fastq(sample)

    # THEN assert SPRING file exists
    assert spring_file.exists()

    # THEN assert that the FASTQ files are NOT removed
    assert fastq_first.exists()
    assert fastq_second.exists()
