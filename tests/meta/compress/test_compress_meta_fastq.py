"""Tests for FASTQ part of meta compress api"""
import logging
import mock


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

    # WHEN Compressing the fastq files for the case
    res = compress_api.compress_fastq(sample)

    # THEN assert compression succeded
    assert res is False
    # THEN assert that the correct information is communicated
    assert f"FASTQ to SPRING not possible for {sample}" in caplog.text


def test_compress_case_fastq_compression_pending(
    populated_compress_fastq_api, sample, compression_object, caplog
):
    """Test to compress all FASTQ files for a sample when compression is pending

    The program should not compress any files since the compression is pending for a sample, but
    should still return True since it is pending.
    """
    caplog.set_level(logging.DEBUG)
    compress_api = populated_compress_fastq_api
    # GIVEN that the pending file exists
    compression_object.pending_path.touch()

    # WHEN compressing the FASTQ files for the case
    compression_has_started = compress_api.compress_fastq(sample)

    # THEN the function returns True
    assert compression_has_started is True
    # THEN assert that the correct information is communicated
    assert f"FASTQ to SPRING not possible for {sample}" in caplog.text


@mock.patch("cg.apps.crunchy.crunchy.CrunchyAPI.is_fastq_compression_possible")
def test_compress_case_fastq_compression_not_pending(
    mock_function, populated_compress_fastq_api, sample, compression_object, caplog
):
    """Test to compress all FASTQ files for a sample when compression not pending, but compression
    is not possible for other reasons. The output should be False
    """
    caplog.set_level(logging.DEBUG)
    compress_api = populated_compress_fastq_api
    # GIVEN that the compression is not possible and pending file does not exists
    assert compression_object.pending_path.exists() is False
    mock_function.return_value = False
    # WHEN compressing the FASTQ files for the case
    compression_has_started = compress_api.compress_fastq(sample)

    # THEN the function returns False
    assert compression_has_started is False
    # THEN assert that the correct information is communicated
    assert f"FASTQ to SPRING not possible for {sample}" in caplog.text
