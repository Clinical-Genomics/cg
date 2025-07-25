"""Tests for cleaning FASTQ files."""

from datetime import datetime
import logging
from pathlib import Path
from typing import Generator
from unittest import mock

from _pytest.logging import LogCaptureFixture
from housekeeper.store.models import File, Version

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import SequencingFileTag
from cg.constants.archiving import PDC_ARCHIVE_LOCATION
from cg.meta.compress import files
from cg.meta.compress.compress import CompressAPI
from cg.models.compression_data import CompressionData
from cg.store.models import Case, Sample
from cg.store.store import Store

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
    fastq: dict[str, dict] = files.get_fastq_files(sample_id=sample_id, version_obj=hk_version)
    run: str = list(fastq.keys())[0]
    compression: CompressionData = fastq[run]["compression_data"]

    # WHEN updating Housekeeper with compressed FASTQ files
    compress_api.update_fastq_hk(
        sample_id=sample_id,
        compression_obj=compression,
        hk_fastq_first=fastq[run]["hk_first"],
        hk_fastq_second=fastq[run]["hk_second"],
        archive_location=PDC_ARCHIVE_LOCATION,
    )

    # THEN assert that the SPRING files have been added to Housekeeper
    hk_spring_files: list[File] = list(real_housekeeper_api.files(tags=[SequencingFileTag.SPRING]))
    hk_spring_metadata_files: list[File] = list(
        real_housekeeper_api.files(tags=[SequencingFileTag.SPRING_METADATA])
    )

    # THEN assert that the Spring files and Spring metadata files have had the fastq file tags transferred
    for spring_file in [hk_spring_files, hk_spring_metadata_files]:
        assert spring_file
        for tag_name in [tag.name for tag in fastq[run]["hk_first"].tags]:
            if tag_name != SequencingFileTag.FASTQ:
                assert tag_name in spring_file.tags

    # THEN assert that the spring files have been tagged with the archive location
    for spring_file in hk_spring_files:
        assert PDC_ARCHIVE_LOCATION in [tag.name for tag in spring_file.tags]

    # THEN assert that the SPRING files have been added to bundles directory
    for spring_file in [hk_spring_files[0].path, hk_spring_metadata_files[0].path]:
        assert Path(root_path, spring_file).exists()

    # THEN assert that the FASTQ files are removed from Housekeeper
    hk_fastq_files: list[File] = list(hk_api.files(tags=[SequencingFileTag.FASTQ]))
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
    populated_compress_fastq_api.clean_fastq(
        sample_id=sample, archive_location=PDC_ARCHIVE_LOCATION
    )

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
    populated_compress_fastq_api.clean_fastq(
        sample_id=sample, archive_location=PDC_ARCHIVE_LOCATION
    )

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
    populated_compress_fastq_api.clean_fastq(
        sample_id=sample, archive_location=PDC_ARCHIVE_LOCATION
    )

    # THEN assert SPRING file exists
    assert spring_file.exists()

    # THEN assert that the FASTQ files are NOT removed
    assert fastq_first.exists()
    assert fastq_second.exists()


def test_clean_fastq_files_for_samples(
    populated_compress_fastq_api: MockCompressAPI,
    helpers: StoreHelpers,
    base_store: Store,
):
    """Test to clean selected FASTQ files."""

    # GIVEN a sample linked to two cases one being not eligible for cleaning
    sample: Sample = helpers.add_sample(store=base_store, internal_id="sample1")
    old_case: Case = helpers.add_case_with_sample(
        base_store=base_store, case_id="case1", sample_id="sample1"
    )
    old_case.created_at = datetime(2023, 1, 1, 12, 0, 0)
    new_case: Case = helpers.add_case_with_sample(
        base_store=base_store, case_id="case2", sample_id="sample1"
    )
    new_case.created_at = datetime.now()
    sample.cases = [old_case, new_case]

    # WHEN calling clean_fastq_files_for_samples with a days_back threshold
    with mock.patch.object(CompressAPI, "clean_fastq") as clean_fastq_mock:
        populated_compress_fastq_api.clean_fastq_files_for_samples(
            samples=[sample],
            days_back=60,
        )
        # THEN assert that the clean_fastq_mock was not called
        clean_fastq_mock.assert_not_called()


def test_clean_fastq_files_for_samples_failure(
    populated_compress_fastq_api: MockCompressAPI,
    helpers: StoreHelpers,
    base_store: Store,
):
    """Test to clean selected FASTQ files with a failure."""
    # GIVEN a case with a sample
    case: Case = helpers.add_case_with_sample(
        base_store=base_store, case_id="case1", sample_id="sample1"
    )
    sample: Sample = case.samples[0]
    # GIVEN that an exception is raised when calling clean_fastq
    with mock.patch.object(CompressAPI, "clean_fastq") as clean_fastq_mock:
        clean_fastq_mock.side_effect = Exception()
        # WHEN calling clean_fastq_files_for_samples
        result: bool = populated_compress_fastq_api.clean_fastq_files_for_samples(
            samples=[sample],
            days_back=60,
        )
        # THEN assert that clean_fastq_files_for_samples returns False
        assert not result


def test_clean_fastq_files_for_samples_continues_after_failure(
    populated_compress_fastq_api: MockCompressAPI,
    helpers: StoreHelpers,
    base_store: Store,
):
    """Test that clean_fastq_files_for_samples continues after failure."""
    # GIVEN a case with two samples
    case: Case = helpers.add_case_with_sample(
        base_store=base_store, case_id="case1", sample_id="sample1"
    )
    sample1: Sample = case.samples[0]
    sample2: Sample = helpers.add_sample(store=base_store, internal_id="sample2")
    sample2.cases = [case]

    # GIVEN that an exception is raised when calling clean_fastq for sample1 but not for sample2
    with mock.patch.object(CompressAPI, "clean_fastq") as clean_fastq_mock:
        clean_fastq_mock.side_effect = [Exception(), None]
        # WHEN calling clean_fastq_files_for_samples
        result: bool = populated_compress_fastq_api.clean_fastq_files_for_samples(
            samples=[sample1, sample2],
            days_back=60,
        )
        # THEN assert that clean_fastq failed for sample1
        clean_fastq_mock.assert_any_call(
            sample_id=sample1.internal_id,
            archive_location=PDC_ARCHIVE_LOCATION,
        )
        # THEN assert that clean_fastq succeeded for sample2
        clean_fastq_mock.assert_any_call(
            sample_id=sample2.internal_id,
            archive_location=PDC_ARCHIVE_LOCATION,
        )

        # THEN assert that clean_fastq_files_for_samples returns False
        assert not result
