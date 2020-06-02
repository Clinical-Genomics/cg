"""Tests for fastq part of meta compress api"""

from cg.apps.hk import HousekeeperAPI


def test_get_fastq_files_no_version(compress_api):
    """test get_fastq_files method when no version is found in hk"""

    # GIVEN a sample id
    sample_id = "test_sample"
    # GIVEN a hk_api that returns None for final version
    compress_api.hk_api._last_version = None

    # WHEN fetching fastq files
    fastq_dict = compress_api.get_fastq_files(sample_id=sample_id)

    # THEN assert that None was returned since there was no version object found
    assert fastq_dict is None


def test_get_fastq_files_no_files(compress_api, mocker):
    """test get_fastq_files method when no files are found"""

    # GIVEN a sample_id
    sample_id = "test_sample"
    # GIVEN a hk that returns an empty list of files
    mocker.patch.object(HousekeeperAPI, "get_files", return_value=[])

    # WHEN fetching the fastq files
    fastq_dict = compress_api.get_fastq_files(sample_id=sample_id)

    # THEN assert that None is returned since there where not two files
    assert fastq_dict is None


def test_get_fastq_files(compress_api, compress_hk_bam_bundle, sample, helpers):
    """test get_fastq_files method when there are fastq files"""

    # GIVEN a sample_id and a hk api populated with fastq bundle
    hk_api = compress_api.hk_api
    helpers.ensure_hk_bundle(hk_api, compress_hk_bam_bundle)

    # WHEN fetching the fastq files
    fastq_dict = compress_api.get_fastq_files(sample_id=sample)
    print(fastq_dict)

    # THEN the fastq files will be in the dictionary
    assert set(fastq_dict.keys()) == set(["fastq_first_file", "fastq_second_file"])
