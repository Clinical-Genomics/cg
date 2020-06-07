"""Tests for cleaning fastq files"""
import logging


def test_remove_fastqs(compress_api, fastq_files, fastq_flag_file, caplog):
    """ Test remove_bam method"""
    caplog.set_level(logging.DEBUG)
    fastq_first_file = fastq_files["fastq_first_path"]
    fastq_second_file = fastq_files["fastq_second_path"]
    # GIVEN existing fastq and flag file
    assert fastq_first_file.exists()
    assert fastq_second_file.exists()
    assert fastq_flag_file.exists()
    # GIVEN a crunchy api where fastq compression is done
    crunchy_api = compress_api.crunchy_api
    crunchy_api.set_fastq_compression_done_all()

    # WHEN calling remove_fastq
    compress_api.remove_fastq(fastq_first=fastq_first_file, fastq_second=fastq_second_file)

    # THEN the assert that the fastq-files and flag-file should not exist
    assert not fastq_first_file.exists()
    assert not fastq_second_file.exists()
    assert not fastq_flag_file.exists()
    expected_output = f"Will remove {fastq_first_file}, {fastq_second_file}, and {fastq_flag_file}"
    assert expected_output in caplog.text
    assert f"Fastq files removed" in caplog.text


# def test_update_hk_fastq(real_housekeeper_api, compress_hk_fastq_bundle, spring_file, helpers):
#     """ Test to update the fastq paths in housekeeper"""
#     hk_bundle = compress_hk_fastq_bundle
#     helpers.ensure_hk_bundle(real_housekeeper_api, hk_bundle)
#     bundle_name = hk_bundle["name"]
#     latest_version = real_housekeeper_api.last_version(bundle_name)
#     print(repr(latest_version))
#     print(latest_version.files)
#     print(real_housekeeper_api)
#     assert 0
#     hk_api = compress_api.hk_api
#     compress_api.crunchy_api.set_bam_compression_done_all()
#     # GIVEN a empty hk api
#     assert len(hk_api.files()) == 0
#     # GIVEN a case-id and a compress api
#     case_id = "test-case"
#
#     # WHEN updating hk
#     compress_api.update_hk(case_id=case_id, bam_dict=bam_dict)
#
#     # THEN add_file should have been called 6 times (two for every case)
#     assert len(hk_api.files()) == 6
