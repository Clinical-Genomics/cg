"""Tests for FASTQ part of meta compress api"""

import logging
from pathlib import Path
from unittest import mock
from unittest.mock import Mock, create_autospec

import pytest
from pytest_mock import MockerFixture

from cg.constants import Workflow
from cg.meta.compress import CompressAPI
from cg.models.compression_data import CaseCompressionData, CompressionData, SampleCompressionData
from cg.store.models import Case, IlluminaFlowCell, IlluminaSequencingRun, Sample
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


def test_compress_case_fastq_one_sample(populated_compress_fastq_api, sample, caplog):
    """Test to compress all FASTQ files for a sample"""
    caplog.set_level(logging.DEBUG)
    compress_api = populated_compress_fastq_api
    compress_api.crunchy_api.set_dry_run(True)
    # GIVEN a populated compress api

    # WHEN Compressing the bam files for the case
    with mock.patch.object(CompressAPI, "_is_spring_archived", return_value=False):
        result = compress_api.compress_fastq(sample)

        # THEN assert compression succeded
        assert result is True
        # THEN assert that the correct information is communicated
        assert "Compressing" in caplog.text
        # THEN assert that the correct information is communicated
        assert "to SPRING format" in caplog.text


def test_compress_fastq_compression_done(
    populated_compress_fastq_api, compression_object, sample, caplog
):
    """Test to compress all FASTQ files for a sample when compression is already completed

    The program should not compress any files since the compression is done for a sample
    """
    caplog.set_level(logging.DEBUG)
    # GIVEN a populated compress api
    compress_api = populated_compress_fastq_api
    # GIVEN that the spring file exists (compression is done)
    compression_object.spring_path.touch()

    # WHEN Compressing the bam files for the case
    with mock.patch.object(CompressAPI, "_is_spring_archived", return_value=False):
        result = compress_api.compress_fastq(sample)

        # THEN assert compression succeded
        assert result is False
        # THEN assert that the correct information is communicated
        assert f"FASTQ to SPRING not possible for {sample}" in caplog.text


def test_compress_sample_fastq_compression_pending(
    populated_compress_fastq_api, sample, compression_object, caplog
):
    """Test to compress all FASTQ files for a sample when compression is pending

    The program should not compress any files since the compression is pending for a sample
    """
    caplog.set_level(logging.DEBUG)
    compress_api = populated_compress_fastq_api
    # GIVEN that the pending flag exists
    compression_object.pending_path.touch()

    # WHEN compressing the FASTQ files for the case
    with mock.patch.object(CompressAPI, "_is_spring_archived", return_value=False):
        result = compress_api.compress_fastq(sample)

        # THEN assert compression returns False
        assert result is False
        # THEN assert that the correct information is communicated
        assert f"FASTQ to SPRING not possible for {sample}" in caplog.text


def test_compress_sample_fastq_archived_spring_file(
    populated_compress_fastq_api, sample, compression_object, caplog
):
    """Test to compress all FASTQ files for a sample when the Spring file is archived

    The program should not compress any files since the Spring file already exists
    """
    caplog.set_level(logging.DEBUG)
    compress_api = populated_compress_fastq_api
    # GIVEN that the pending flag exists
    compression_object.pending_path.touch()

    # WHEN compressing the FASTQ files for the case
    with mock.patch.object(CompressAPI, "_is_spring_archived", return_value=True):
        result = compress_api.compress_fastq(sample)

        # THEN assert compression returns False
        assert result is False
        # THEN assert that the correct information is communicated
        assert f"FASTQ to SPRING not possible for {sample}" in caplog.text


def test_get_microsalt_case_compression_data(
    compress_api: CompressAPI, sample_compression_data: SampleCompressionData, mocker: MockerFixture
):
    """
    Test that the case compression data from a microSALT case with samples, some of which don't
    have reads, only contains the sample compression data of the samples that have reads.
    """
    # GIVEN a CompressAPI instance

    # GIVEN a microSALT case with 3 samples, only one of them has reads
    sample_with_reads: Mock[Sample] = create_autospec(Sample)
    sample_with_reads.has_reads = True
    sample_with_reads.internal_id = "sample_with_reads"

    sample_without_reads: Mock[Sample] = create_autospec(Sample)
    sample_without_reads.has_reads = False
    sample_without_reads.internal_id = "sample_without_reads"

    case: Mock[Case] = create_autospec(Case)
    case.data_analysis = Workflow.MICROSALT
    case.samples = [sample_with_reads, sample_without_reads, sample_without_reads]
    case.internal_id = "case_with_samples"

    # GIVEN a sample compression data for the sample with reads
    mocker.patch.object(
        compress_api, "get_sample_compression_data", return_value=sample_compression_data
    )

    # WHEN getting the case compression data
    case_compression_data: CaseCompressionData = compress_api.get_case_compression_data(case)

    # THEN the case compression data should only contain data for the sample that has reads
    assert case_compression_data.sample_compression_data == [sample_compression_data]


@pytest.mark.parametrize(
    "workflow, has_reads, expected",
    [
        (Workflow.MICROSALT, False, True),
        (Workflow.MUTANT, True, False),
        (Workflow.RNAFUSION, False, False),
        (Workflow.RNAFUSION, True, False),
    ],
)
def test_should_skip_sample(
    workflow: Workflow, has_reads: bool, expected: bool, compress_api: CompressAPI
):
    """Test that the skip sample function returns the expected value."""
    # GIVEN a case and a sample and a CompressAPI instance
    case: Mock[Case] = create_autospec(Case)
    case.data_analysis = workflow
    sample: Mock[Sample] = create_autospec(Sample)
    sample.has_reads = has_reads

    # WHEN checking if the sample should be skipped
    result: bool = compress_api._should_skip_sample(case=case, sample=sample)

    # THEN assert that the result is as expected
    assert result == expected


def _add_matching_sequencing_metrics(
    store: Store, helpers: StoreHelpers, flow_cell_id: str, sample_id: str, lane: int
) -> None:
    flow_cell: IlluminaFlowCell = helpers.add_illumina_flow_cell(
        store=store, flow_cell_id=flow_cell_id
    )
    sequencing_run: IlluminaSequencingRun = helpers.add_illumina_sequencing_run(
        store=store, flow_cell=flow_cell
    )
    helpers.add_sample(store=store, internal_id=sample_id)
    helpers.add_illumina_sample_sequencing_metrics_object(
        store=store, sample_id=sample_id, sequencing_run=sequencing_run, lane=lane
    )


def test_get_resources_for_run_scales_with_reads(
    compress_api: CompressAPI, base_store: Store, helpers: StoreHelpers
):
    """Test that a matching sequencing metrics row yields scaled memory/minutes."""
    # GIVEN a compress API pointed at a store with matching sequencing metrics for a run
    compress_api.status_db = base_store
    flow_cell_id, sample_id, lane = "23M7GHLT4", "ACC20498A8", 4
    _add_matching_sequencing_metrics(base_store, helpers, flow_cell_id, sample_id, lane)
    compression_obj = CompressionData(Path(f"{flow_cell_id}_{sample_id}_S52_L00{lane}"))

    # WHEN getting resources for the run (100 reads recorded)
    memory, minutes = compress_api._get_resources_for_run(
        compression_obj,
        reads_per_gb=10,
        min_gb=1,
        max_gb=100,
        reads_per_minute=20,
        min_minutes=1,
        max_minutes=100,
    )

    # THEN memory and minutes are scaled according to the read count
    assert memory == 10
    assert minutes == 5

    # THEN crunchy_api's own config values are left untouched - it is shared across all runs
    assert compress_api.crunchy_api.fallback_memory != 10
    assert compress_api.crunchy_api.fallback_minutes != 5


def test_get_resources_for_run_no_matching_metrics(compress_api: CompressAPI, base_store: Store):
    """Test that a run with no matching sequencing metrics falls back to crunchy_api's config."""
    # GIVEN a compress API pointed at a store with no matching sequencing metrics
    compress_api.status_db = base_store
    compression_obj = CompressionData(Path("not_a_valid_name"))

    # WHEN getting resources for the run
    memory, minutes = compress_api._get_resources_for_run(
        compression_obj,
        reads_per_gb=10,
        min_gb=1,
        max_gb=100,
        reads_per_minute=20,
        min_minutes=1,
        max_minutes=100,
    )

    # THEN both memory and minutes fall back to crunchy_api's configured fallback values - the
    # caller never has to handle a missing value itself
    assert memory == compress_api.crunchy_api.fallback_memory
    assert minutes == compress_api.crunchy_api.fallback_minutes
