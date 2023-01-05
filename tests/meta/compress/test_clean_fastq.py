"""Tests for cleaning FASTQ files"""
import logging

import pytest

from cg.meta.compress import files


@pytest.mark.compress_meta
def test_remove_fastqs(compress_api, compression_object, caplog):
    """Test remove_fastq method

    This method should remove FASTQ files since compression is completed
    """
    caplog.set_level(logging.DEBUG)
    # GIVEN existing FASTQ and flag file
    fastq_first = compression_object.fastq_first
    fastq_second = compression_object.fastq_second
    fastq_first.touch()
    fastq_second.touch()
    compression_object.spring_metadata_path.touch()

    # WHEN calling remove_fastq
    compress_api.remove_fastq(fastq_first=fastq_first, fastq_second=fastq_second)

    # THEN the assert that the FASTQ-files are deleted
    assert not fastq_first.exists()
    assert not fastq_second.exists()
    # THEN assert that the flag file is still there since this holds important information
    assert compression_object.spring_metadata_path.exists()
    expected_output = f"Will remove {fastq_first} and {fastq_second}"
    assert expected_output in caplog.text
    assert "FASTQ files removed" in caplog.text


@pytest.mark.compress_meta
def test_update_hk_fastq(real_housekeeper_api, compress_hk_fastq_bundle, compress_api, helpers):
    """Test to update the FASTQ and SPRING paths in housekeeper after completed compression

    This will test so that the FASTQ files are replaced by a SPRING file and a SPRING metadata file
    """
    # GIVEN real housekeeper api populated with a housekeeper bundle
    hk_bundle = compress_hk_fastq_bundle
    sample_id = hk_bundle["name"]
    hk_api = real_housekeeper_api
    helpers.ensure_hk_bundle(real_housekeeper_api, hk_bundle)
    compress_api.hk_api = hk_api

    # GIVEN that there are some FASTQ files in housekeeper
    hk_fastq_files = list(hk_api.files(tags=["fastq"]))
    assert hk_fastq_files
    # GIVEN that there are no SPRING files in housekeeper
    hk_spring_file = list(hk_api.files(tags=["spring"]))
    assert not hk_spring_file
    hk_fastq_flag_file = list(hk_api.files(tags=["spring-metadata"]))
    assert not hk_fastq_flag_file
    # GIVEN a housekeeper version
    version_obj = compress_api.hk_api.get_latest_bundle_version(bundle_name=sample_id)
    fastq_dict = files.get_fastq_files(sample_id=sample_id, version_obj=version_obj)
    run = list(fastq_dict.keys())[0]
    compression_obj = fastq_dict[run]["compression_data"]

    # WHEN updating hk
    compress_api.update_fastq_hk(
        sample_id=sample_id,
        compression_obj=compression_obj,
        hk_fastq_first=fastq_dict[run]["hk_first"],
        hk_fastq_second=fastq_dict[run]["hk_second"],
    )

    # THEN assert that the FASTQ files are removed from housekeeper
    hk_fastq_files = list(hk_api.files(tags=["fastq"]))
    assert not hk_fastq_files
    # THEN assert that the SPRING file and the metadata file is added to housekeeper
    hk_spring_file = list(real_housekeeper_api.files(tags=["spring"]))
    assert hk_spring_file
    hk_fastq_flag_file = list(real_housekeeper_api.files(tags=["spring-metadata"]))
    assert hk_fastq_flag_file


@pytest.mark.compress_meta
@pytest.mark.clean_fastq
def test_cli_clean_fastqs_removed(populated_compress_fastq_api, compression_files, sample):
    """Test to clean FASTQs after a succesfull FASTQ compression

    Files should be cleaned since the compression is completed
    """
    compress_api = populated_compress_fastq_api
    spring_file = compression_files.spring_file
    spring_metadata_file = compression_files.spring_metadata_file
    fastq_first = compression_files.fastq_first_file
    fastq_second = compression_files.fastq_second_file
    # GIVEN that the SPRING compression files exist
    assert spring_file.exists()
    assert spring_metadata_file.exists()
    # GIVEN that the FASTQ files exists
    assert fastq_first.exists()
    assert fastq_second.exists()

    # WHEN running the clean command
    compress_api.clean_fastq(sample)

    # THEN assert SPRING files exists
    assert spring_file.exists()
    assert spring_metadata_file.exists()
    # THEN assert that the FASTQ files are removed
    assert not fastq_first.exists()
    assert not fastq_second.exists()


@pytest.mark.compress_meta
@pytest.mark.clean_fastq
def test_cli_clean_fastqs_no_spring_metadata(
    populated_compress_fastq_api, sample, compression_files
):
    """Test to clean FASTQs when SPRING compression is not finished

    No files should be cleaned since compression is not completed
    """
    compress_api = populated_compress_fastq_api
    spring_file = compression_files.spring_file
    spring_metadata_file = compression_files.spring_metadata_path
    fastq_first = compression_files.fastq_first_file
    fastq_second = compression_files.fastq_second_file
    # GIVEN that the SPRING compression file exist
    assert spring_file.exists()
    # GIVEN that the SPRING metadata file does not exist
    assert not spring_metadata_file.exists()

    # WHEN running the clean command
    compress_api.clean_fastq(sample)

    # THEN assert SPRING file exists
    assert spring_file.exists()
    # THEN assert that the FASTQ files are NOT removed
    assert fastq_first.exists()
    assert fastq_second.exists()


@pytest.mark.compress_meta
@pytest.mark.clean_fastq
def test_cli_clean_fastqs_pending_compression_metadata(
    populated_compress_fastq_api, sample, compression_files
):
    """Test to clean FASTQs when SPRING compression is pending

    No files should be cleaned since compression is not completed
    """
    compress_api = populated_compress_fastq_api
    spring_file = compression_files.spring_file
    fastq_first = compression_files.fastq_first_file
    fastq_second = compression_files.fastq_second_file

    # GIVEN that the SPRING compression file exist
    assert spring_file.exists()
    crunchy_flag_file = compression_files.pending_file
    assert crunchy_flag_file.exists()

    # WHEN running the clean command
    compress_api.clean_fastq(sample)

    # THEN assert SPRING file exists
    assert spring_file.exists()
    # THEN assert that the FASTQ files are NOT removed
    assert fastq_first.exists()
    assert fastq_second.exists()
