"""Tests for the compression files module"""
import logging


from cg.meta.compress import files
from cg.models import CompressionData


def test_get_fastq_files(populated_compress_fastq_api, sample):
    """Test get_fastq_files method when there are FASTQ files"""
    compress_api = populated_compress_fastq_api
    # GIVEN a sample_id and a hk api populated with fastq bundle

    # WHEN fetching the fastq files
    version_obj = compress_api.hk_api.get_latest_bundle_version(bundle_name=sample)
    fastq_dict = files.get_fastq_files(sample_id=sample, version_obj=version_obj)
    run = list(fastq_dict.keys())[0]

    # THEN the fastq files will be in the dictionary
    assert set(fastq_dict[run].keys()) == set(["compression_data", "hk_first", "hk_second"])
    # THEN assert that a CompressionData object was returned
    assert isinstance(fastq_dict[run]["compression_data"], CompressionData)


def test_get_fastq_files_no_files(compress_api, sample_hk_bundle_no_files, sample, helpers, caplog):
    """Test get_fastq_files method when no FASTQ files are found"""
    caplog.set_level(logging.DEBUG)
    # GIVEN a sample_id
    sample_id = sample
    hk_api = compress_api.hk_api
    # GIVEN a bundle without files
    assert sample_hk_bundle_no_files["files"] == []
    helpers.ensure_hk_bundle(hk_api, sample_hk_bundle_no_files)

    # WHEN fetching the fastq files
    version_obj = compress_api.hk_api.get_latest_bundle_version(bundle_name=sample)
    fastq_dict = files.get_fastq_files(sample_id=sample_id, version_obj=version_obj)

    # THEN assert that None is returned since there where not two files
    assert fastq_dict is None
    # THEN assert that the correct information is returned
    assert f"Could not find FASTQ files for {sample}" in caplog.text
