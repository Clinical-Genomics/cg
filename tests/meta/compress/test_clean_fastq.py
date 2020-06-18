"""Tests for cleaning fastq files"""
import logging

from cg.meta.compress import files


def test_remove_fastqs(compress_api, fastq_files, fastq_flag_file, caplog):
    """ Test remove_fastq method

    This method should remove fastq files since compression is completed
    """
    caplog.set_level(logging.DEBUG)
    fastq_first_file = fastq_files["fastq_first_path"]
    fastq_second_file = fastq_files["fastq_second_path"]
    # GIVEN existing fastq and flag file
    assert fastq_first_file.exists()
    assert fastq_second_file.exists()
    assert fastq_flag_file.exists()

    # WHEN calling remove_fastq
    compress_api.remove_fastq(fastq_first=fastq_first_file, fastq_second=fastq_second_file)

    # THEN the assert that the fastq-files are deleted
    assert not fastq_first_file.exists()
    assert not fastq_second_file.exists()
    # THEN assert that the flag file is still there since this holds important information
    assert fastq_flag_file.exists()
    expected_output = f"Will remove {fastq_first_file} and {fastq_second_file}"
    assert expected_output in caplog.text
    assert f"Fastq files removed" in caplog.text


def test_update_hk_fastq(real_housekeeper_api, compress_hk_fastq_bundle, compress_api, helpers):
    """ Test to update the fastq paths after completed compression in housekeeper

    This will test so that the fastq files are replaced by a spring file and a spring metadata file
    """
    # GIVEN real housekeeper api populated with a housekeeper bundle
    hk_bundle = compress_hk_fastq_bundle
    sample_id = hk_bundle["name"]
    hk_api = real_housekeeper_api
    helpers.ensure_hk_bundle(real_housekeeper_api, hk_bundle)
    sample_id = hk_bundle["name"]
    compress_api.hk_api = hk_api

    # GIVEN that there are some fastq files in housekeeper
    hk_fastq_files = list(hk_api.files(tags=["fastq"]))
    assert hk_fastq_files
    # GIVEN that there are no spring files in housekeeper
    hk_spring_file = list(hk_api.files(tags=["spring"]))
    assert not hk_spring_file
    hk_fastq_flag_file = list(hk_api.files(tags=["spring-metadata"]))
    assert not hk_fastq_flag_file
    # GIVEN a housekeeper version
    version_obj = compress_api.get_latest_version(sample_id)
    fastq_dict = files.get_fastq_files(sample_id=sample_id, version_obj=version_obj)
    hk_fastq_first = fastq_dict["fastq_first_file"]["hk_file"]
    hk_fastq_second = fastq_dict["fastq_second_file"]["hk_file"]

    # WHEN updating hk
    compress_api.update_fastq_hk(
        sample_id=sample_id, hk_fastq_first=hk_fastq_first, hk_fastq_second=hk_fastq_second
    )

    # THEN assert that the fastq files are removed from housekeeper
    hk_fastq_files = list(real_housekeeper_api.files(tags=["fastq"]))
    assert not hk_fastq_files
    # THEN assert that the spring file and the metadata file is added to housekeeper
    hk_spring_file = list(real_housekeeper_api.files(tags=["spring"]))
    assert hk_spring_file
    hk_fastq_flag_file = list(real_housekeeper_api.files(tags=["spring-metadata"]))
    assert hk_fastq_flag_file


def test_clean_fastq():
    """Test the clean fastq functionality of the compress api

    The function should check if compression is done and after that cleanup the files that have
    been compressed.
    """
