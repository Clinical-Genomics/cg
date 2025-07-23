"""Tests for FASTQ part of meta compress api"""

import logging
from unittest import mock
from unittest.mock import Mock, create_autospec

import pytest
from pytest_mock import MockerFixture

from cg.constants import Workflow
from cg.meta.compress import CompressAPI
from cg.models.compression_data import CaseCompressionData, SampleCompressionData
from cg.store.models import Case, Sample


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
