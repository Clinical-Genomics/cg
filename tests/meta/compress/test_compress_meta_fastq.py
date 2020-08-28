"""Tests for FASTQ part of meta compress api"""
import logging


def test_compress_case_fastq_one_sample(populated_compress_fastq_api, sample, caplog):
    """Test to compress all FASTQ files for a sample"""
    caplog.set_level(logging.DEBUG)
    compress_api = populated_compress_fastq_api
    compress_api.crunchy_api.set_dry_run(True)
    # GIVEN a populated compress api

    # WHEN Compressing the bam files for the case
    res = compress_api.compress_fastq(sample)

    # THEN assert compression succeded
    assert res is True
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
    res = compress_api.compress_fastq(sample)

    # THEN assert compression succeded
    assert res is False
    # THEN assert that the correct information is communicated
    assert f"FASTQ to SPRING not possible for {sample}" in caplog.text


def test_compress_case_fastq_compression_pending(
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
    res = compress_api.compress_fastq(sample)

    # THEN assert compression returns False
    assert res is False
    # THEN assert that the correct information is communicated
    assert f"FASTQ to SPRING not possible for {sample}" in caplog.text
