"""Tests for cleaning fastq files"""


def test_update_hk_fastq(real_housekeeper_api, compress_hk_fastq_bundle, helpers):
    """ Test to update the bam paths in housekeeper"""
    helpers.ensure_hk_bundle(real_housekeeper_api, compress_hk_fastq_bundle)
    bundle_name = compress_hk_fastq_bundle["name"]
    latest_version = real_housekeeper_api.last_version(bundle_name)
    print(repr(latest_version))
    print(latest_version.files)
    print(real_housekeeper_api)
    assert 0
    mock_compress_func(bam_dict)
    hk_api = compress_api.hk_api
    compress_api.crunchy_api.set_bam_compression_done_all()
    # GIVEN a empty hk api
    assert len(hk_api.files()) == 0
    # GIVEN a case-id and a compress api
    case_id = "test-case"

    # WHEN updating hk
    compress_api.update_hk(case_id=case_id, bam_dict=bam_dict)

    # THEN add_file should have been called 6 times (two for every case)
    assert len(hk_api.files()) == 6
