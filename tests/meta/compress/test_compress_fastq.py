"""Tests for fastq part of meta compress api"""
import logging


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
    assert "There has to be a pair of fastq files" in caplog.text


def test_get_fastq_files(compress_api, compress_hk_fastq_bundle, sample, helpers):
    """test get_fastq_files method when there are fastq files"""

    # GIVEN a sample_id and a hk api populated with fastq bundle
    hk_api = compress_api.hk_api
    helpers.ensure_hk_bundle(hk_api, compress_hk_fastq_bundle)

    # WHEN fetching the fastq files
    fastq_dict = compress_api.get_fastq_files(sample_id=sample)

    # THEN the fastq files will be in the dictionary
    assert set(fastq_dict.keys()) == set(["fastq_first_file", "fastq_second_file"])
