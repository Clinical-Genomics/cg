""" Tests for common functions of the compress API """

from cg.meta.compress import files


def test_get_latest_version_no_housekeeper_files(compress_api, caplog):
    """test get_bam_dict method when there is not case in scout"""

    case_id = "compress_case"
    # GIVEN a case id

    # WHEN getting the version_obj
    res = compress_api.get_latest_version(case_id)

    # THEN assert that None was returned since the case was not found in scout
    assert res is None
    # THEN assert that the correct information is being processed
    assert f"No bundle found for {case_id} in housekeeper" in caplog.text
