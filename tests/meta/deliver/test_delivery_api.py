"""Tests for delivery API"""


def test_get_post_analysis_files(deliver_api):

    # GIVEN a case which exist as bundle in hk
    # GIVEN corresponding houskeeper tags for those files
    case = "case_id"
    deliver_tags = ["case-tag"]

    # WHEN we call get_post_analysis_files with matching case and file-tags and version is no version
    version = None
    bundle_latest_files = deliver_api.get_post_analysis_files(case, version, deliver_tags)

    ## THEN housekeeper files should be returned
    assert bundle_latest_files


def test_get_post_analysis_files_version(timestamp, deliver_api):

    # GIVEN a case which exist as bundle in hk
    # GIVEN corresponding houskeeper tags for those files
    case = "case_id"
    deliver_tags = ["case-tag"]

    # WHEN we call get_post_analysis_files with matching case and file-tags and version is supplied
    version = timestamp

    bundle_version_files = deliver_api.get_post_analysis_files(case, version, deliver_tags)

    # THEN housekeeper files for those tags with the version should be returned
    assert bundle_version_files


def test_get_post_analysis_case_files(deliver_api):

    # GIVEN a case which exist as bundle in hk
    # GIVEN corresponding case houskeeper tags for those files
    case = "case_id"
    deliver_tags = ["case-tag"]

    # WHEN we call get_post_analysis_case_files with matching case and case file-tags and version
    version = None
    case_files = deliver_api.get_post_analysis_case_files(case, version, deliver_tags)

    # THEN we should get those matching files back
    assert case_files


def test_get_post_analysis_case_files_only_sample_tags(deliver_api):

    # GIVEN a case which exist as bundle in hk
    # GIVEN corresponding sample id houskeeper tags for those files
    case = "case_id"
    deliver_tags = ["sample-tag"]

    # WHEN we call get_post_analysis_case_files with matching case and sample file-tags and version
    version = None
    case_files = deliver_api.get_post_analysis_case_files(case, version, deliver_tags)

    # THEN we should get those matching files back
    assert not case_files


def test_get_post_analysis_sample_files(analysis_family, deliver_api):

    # GIVEN a case which exist as bundle in hk
    # GIVEN corresponding houskeeper tags for those files
    case = "case_id"
    sample = analysis_family["samples"][0]["internal_id"]
    deliver_tags = ["sample-tag"]

    # WHEN we call get_post_analysis_sample_files with matching case and file-tags and version
    version = None
    sample_files = deliver_api.get_post_analysis_sample_files(case, sample, version, deliver_tags)

    # THEN we should get those matching files back
    assert sample_files


def test_get_post_analysis_sample_files_only_case_tags(analysis_family, deliver_api):

    # GIVEN a case which exist as bundle in hk
    # GIVEN corresponding houskeeper tags for those files
    case = "case_id"
    sample = analysis_family["samples"][0]["internal_id"]
    deliver_tags = ["case-tag"]

    # WHEN we call get_post_analysis_sample_files with matching case and file-tags and version
    version = None
    sample_files = deliver_api.get_post_analysis_sample_files(case, sample, version, deliver_tags)

    # THEN we should get those matching files back
    assert not sample_files


def test_get_post_analysis_files_root_dir(deliver_api):

    ## WHEN we call get_post_analysis_files_root_dir
    root_dir = deliver_api.get_post_analysis_files_root_dir()

    ## THEN we should get a path back
    assert root_dir
