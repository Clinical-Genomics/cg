"""Tests for fastq part of meta compress api"""
import logging
from pathlib import Path

from cg.constants import FASTQ_FIRST_READ_SUFFIX, FASTQ_SECOND_READ_SUFFIX
from cg.meta.compress import CompressAPI


def test_get_fastq_files_no_version(compress_api, sample, caplog):
    """test get_fastq_files method when no version is found in hk"""

    # GIVEN a sample id
    sample_id = sample
    # GIVEN a hk_api that returns None for final version
    compress_api.hk_api.set_missing_last_version()

    # WHEN fetching fastq files
    fastq_dict = compress_api.get_fastq_files(sample_id=sample_id)

    # THEN assert that None was returned since there was no version object found
    assert fastq_dict is None
    # THEN assert the correct information is displayed
    assert f"No bundle found for {sample_id} in housekeeper" in caplog.text


def test_get_fastq_files_no_files(compress_api, sample_hk_bundle_no_files, sample, helpers, caplog):
    """test get_fastq_files method when no files are found"""
    caplog.set_level(logging.DEBUG)
    # GIVEN a sample_id
    sample_id = sample
    hk_api = compress_api.hk_api
    # GIVEN a bundle without files
    assert sample_hk_bundle_no_files["files"] == []
    helpers.ensure_hk_bundle(hk_api, sample_hk_bundle_no_files)

    # WHEN fetching the fastq files
    fastq_dict = compress_api.get_fastq_files(sample_id=sample_id)

    # THEN assert that None is returned since there where not two files
    assert fastq_dict is None
    # THEN assert that the correct information is returned
    assert "Could not find paired fastq files" in caplog.text


def test_get_fastq_files(populated_compress_fastq_api, sample):
    """test get_fastq_files method when there are fastq files"""
    compress_api = populated_compress_fastq_api
    # GIVEN a sample_id and a hk api populated with fastq bundle

    # WHEN fetching the fastq files
    fastq_dict = compress_api.get_fastq_files(sample_id=sample)

    # THEN the fastq files will be in the dictionary
    assert set(fastq_dict.keys()) == set(["fastq_first_file", "fastq_second_file"])


def test_check_prefixes(sample):
    """test to check if two fastq files belong to the same readpair when they do"""

    # GIVEN two fatq files from the same readpair
    first_fastq = Path(sample) / FASTQ_FIRST_READ_SUFFIX
    second_fastq = Path(sample) / FASTQ_SECOND_READ_SUFFIX

    # WHEN checking if they belong to the same sample
    res = CompressAPI.check_prefixes(first_fastq, second_fastq)

    # THEN assert that the result is true
    assert res is True


def test_compress_case_fastq_one_sample(populated_compress_fastq_api, sample, caplog):
    """Test to compress all fastq files for a sample"""
    caplog.set_level(logging.DEBUG)
    compress_api = populated_compress_fastq_api
    # GIVEN a populated compress api

    # WHEN Compressing the bam files for the case
    res = compress_api.compress_fastq(sample)

    # THEN assert compression succeded
    assert res is True
    # THEN assert that the correct information is communicated
    assert "Compressing" in caplog.text
    # THEN assert that the correct information is communicated
    assert "to SPRING format" in caplog.text
    # THEN assert that the fastq compression was called once
    assert compress_api.crunchy_api.nr_fastq_compressions() == 1


def test_compress_fastq_compression_done(populated_compress_fastq_api, sample, caplog):
    """Test to compress all fastq files for a sample when compression is already completed

    The program should not compress any files since the compression is done for a sample
    """
    caplog.set_level(logging.DEBUG)
    compress_api = populated_compress_fastq_api
    # GIVEN that the compression is done
    compress_api.crunchy_api.set_spring_compression_done()
    # GIVEN a populated compress api

    # WHEN Compressing the bam files for the case
    res = compress_api.compress_fastq(sample)

    # THEN assert compression succeded
    assert res is False
    # THEN assert that the correct information is communicated
    assert f"FASTQ to SPRING compression already done for {sample}" in caplog.text
    # THEN assert that the fastq compression was never called
    assert compress_api.crunchy_api.nr_fastq_compressions() == 0


def test_compress_case_fastq_compression_pending(populated_compress_fastq_api, sample, caplog):
    """Test to compress all fastq files for a sample when compression is pending

    The program should not compress any files since the compression is pending for a sample
    """
    caplog.set_level(logging.DEBUG)
    compress_api = populated_compress_fastq_api
    # GIVEN that the compression is done
    compress_api.crunchy_api.set_spring_compression_pending()
    # GIVEN a populated compress api

    # WHEN Compressing the bam files for the case
    res = compress_api.compress_fastq(sample)

    # THEN assert compression returns False
    assert res is False
    # THEN assert that the correct information is communicated
    assert f"FASTQ to SPRING compression pending for {sample}" in caplog.text
    # THEN assert that the fastq compression was never called
    assert compress_api.crunchy_api.nr_fastq_compressions() == 0
