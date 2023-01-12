"""Tests for cleaning FASTQ files."""
import logging
from pathlib import Path
from typing import Generator, Dict

import pytest

from housekeeper.store.models import Version

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import SequencingFileTag
from cg.meta.compress import files
from tests.cli.compress.conftest import MockCompressAPI
from tests.meta.compress.conftest import MockCompressionData
from tests.store_helpers import StoreHelpers


@pytest.mark.compress_meta
def test_remove_fastqs(
    compress_api: MockCompressAPI, compression_object: MockCompressionData, caplog
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
    expected_output = f"Will remove {fastq_first} and {fastq_second}"
    assert expected_output in caplog.text
    assert "FASTQ files removed" in caplog.text


@pytest.mark.compress_meta
def test_update_hk_fastq(
    real_housekeeper_api: Generator[HousekeeperAPI, None, None],
    compress_hk_fastq_bundle: dict,
    compress_api: MockCompressAPI,
    helpers: StoreHelpers,
):
    """Test to update the FASTQ and SPRING paths in Housekeeper after completed compression."""
    # GIVEN real Housekeeper API populated with a Housekeeper bundle
    sample_id: str = compress_hk_fastq_bundle["name"]
    hk_api: Generator[HousekeeperAPI, None, None] = real_housekeeper_api
    helpers.ensure_hk_bundle(hk_api, compress_hk_fastq_bundle)
    compress_api.hk_api = hk_api

    # GIVEN that there are some FASTQ files in housekeeper
    hk_fastq_files = list(hk_api.files(tags=[SequencingFileTag.FASTQ]))
    assert hk_fastq_files
    # GIVEN that there are no SPRING files in housekeeper
    hk_spring_files = list(hk_api.files(tags=[SequencingFileTag.SPRING]))
    assert not hk_spring_files
    hk_fastq_flag_files = list(hk_api.files(tags=[SequencingFileTag.SPRING_METADATA]))
    assert not hk_fastq_flag_files
    # GIVEN a housekeeper version
    hk_version: Version = compress_api.hk_api.get_latest_bundle_version(bundle_name=sample_id)
    fastq: Dict[str, dict] = files.get_fastq_files(sample_id=sample_id, version_obj=hk_version)
    run = list(fastq.keys())[0]
    compression = fastq[run]["compression_data"]

    # WHEN updating hk
    compress_api.update_fastq_hk(
        sample_id=sample_id,
        compression_obj=compression,
        hk_fastq_first=fastq[run]["hk_first"],
        hk_fastq_second=fastq[run]["hk_second"],
    )

    # THEN assert that the FASTQ files are removed from Housekeeper
    hk_fastq_files = list(hk_api.files(tags=[SequencingFileTag.FASTQ]))
    assert not hk_fastq_files
    # THEN assert that the SPRING file and the metadata file is added to Housekeeper
    hk_spring_files = list(real_housekeeper_api.files(tags=[SequencingFileTag.SPRING]))
    assert hk_spring_files
    hk_fastq_flag_files = list(real_housekeeper_api.files(tags=[SequencingFileTag.SPRING_METADATA]))
    assert hk_fastq_flag_files


@pytest.mark.compress_meta
@pytest.mark.clean_fastq
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


@pytest.mark.compress_meta
@pytest.mark.clean_fastq
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


@pytest.mark.compress_meta
@pytest.mark.clean_fastq
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
