"""Tests for bam part of meta compress api"""
import logging
from pathlib import Path


def test_get_bam_dict(compress_api, compress_scout_case, compress_hk_bam_bundle, case_id, helpers):
    """test get_bam_dict method"""

    # GIVEN a scout api that returns some case info
    scout_api = compress_api.scout_api
    scout_api.add_mock_case(compress_scout_case)
    # GIVEN a hk api that returns some data
    hk_api = compress_api.hk_api
    helpers.ensure_hk_bundle(hk_api, compress_hk_bam_bundle)

    # WHEN getting bam-files

    bam_dict = compress_api.get_bam_dict(case_id=case_id)

    # THEN the bam-files for the samples will be in the dictionary
    assert set(bam_dict.keys()) == set(["sample_1", "sample_2", "sample_3"])


def test_compress_case_bam_no_scout_case(compress_api, compress_hk_bam_bundle, helpers, caplog):
    """Test to compress the bam files of a case when the scout does not exist in scout"""
    caplog.set_level(logging.DEBUG)
    # GIVEN a scout api that have no cases
    case_id = compress_hk_bam_bundle["name"]
    scout_api = compress_api.scout_api
    assert not scout_api.get_cases(case_id)
    # GIVEN a hk api that returns some data
    hk_api = compress_api.hk_api
    helpers.ensure_hk_bundle(hk_api, compress_hk_bam_bundle)

    # WHEN Compressing the bam files for the case
    res = compress_api.compress_case_bam(case_id)

    # THEN assert compression could not complete
    assert res is False
    # THEN assert that the correct information is communicated
    assert f"{case_id} not found in scout" in caplog.text


def test_compress_case_bam(populated_compress_api, case_id, caplog):
    """Test to compress all bam files for a case"""
    caplog.set_level(logging.DEBUG)
    # GIVEN a populated compress api

    # WHEN Compressing the bam files for the case
    res = populated_compress_api.compress_case_bam(case_id)

    # THEN assert compression succeded
    assert res is True
    # THEN assert that the correct information is communicated
    assert "Compressing" in caplog.text


def test_compress_case_bam_compression_not_possible(
    populated_compress_api, compress_hk_bam_bundle, case_id, caplog
):
    """Test to compress all bam files for a case when compression is not possible for one sample"""
    caplog.set_level(logging.DEBUG)
    # GIVEN an existing bam file
    for file_info in compress_hk_bam_bundle["files"]:
        if "bam" in file_info["tags"]:
            bam_path = Path(file_info["path"])
    assert bam_path.exists()
    # GIVEN a that compression is not possible for one sample
    populated_compress_api.crunchy_api.set_compression_not_possible(bam_path)

    # WHEN Compressing the bam files for the case
    res = populated_compress_api.compress_case_bam(case_id)

    # THEN assert compression succeded
    assert res is False
    # THEN assert that the correct information is communicated
    assert "BAM to CRAM compression not possible" in caplog.text
