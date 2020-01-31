"""Tests for delivery API"""


def test_get_post_analysis_files(analysis_family, deliver_api):

    # GIVEN a family which exist as bundle in hk
    # GIVEN corresponding houskeeper tags for those files
    family = analysis_family["internal_id"]
    deliver_tags = ["case-tag"]

    # WHEN we call get_post_analysis_files with matching case and file-tags and version is no version
    version = None
    bundle_latest_files = deliver_api.get_post_analysis_files(
        family, version, deliver_tags
    )

    ## THEN housekeeper files should be returned
    assert bundle_latest_files


def test_get_post_analysis_files_version(analysis_family, deliver_api):

    # GIVEN a family which exist as bundle in hk
    # GIVEN corresponding houskeeper tags for those files
    family = analysis_family["internal_id"]
    deliver_tags = ["case-tag"]

    # WHEN we call get_post_analysis_files with matching case and file-tags and version is supplied
    version = "a_date"

    bundle_version_files = deliver_api.get_post_analysis_files(
        family, version, deliver_tags
    )

    ## THEN housekeeper files for those tags with the version should be returned
    assert bundle_version_files


def test_get_post_analysis_family_files(analysis_family, deliver_api):

    # GIVEN a family which exist as bundle in hk
    # GIVEN corresponding houskeeper tags for those files
    family = analysis_family["internal_id"]
    deliver_tags = ["case-tag"]

    # WHEN we call get_post_analysis_family_files with matching case and file-tags and version
    version = None
    family_files = deliver_api.get_post_analysis_family_files(
        family, version, deliver_tags
    )

    # THEN we should get those matching files back
    assert family_files


def test_get_post_analysis_family_files_only_sample_tags(analysis_family, deliver_api):

    # GIVEN a family which exist as bundle in hk
    # GIVEN corresponding houskeeper tags for those files
    family = analysis_family["internal_id"]
    deliver_tags = ["sample-tag"]

    # WHEN we call get_post_analysis_family_files with matching case and file-tags and version
    version = None
    family_files = deliver_api.get_post_analysis_family_files(
        family, version, deliver_tags
    )

    # THEN we should get those matching files back
    assert not family_files


def test_get_post_analysis_sample_files(analysis_family, deliver_api):

    # GIVEN a family which exist as bundle in hk
    # GIVEN corresponding houskeeper tags for those files
    family = analysis_family["internal_id"]
    sample = analysis_family["samples"][0]["internal_id"]
    deliver_tags = ["sample-tag"]

    # WHEN we call get_post_analysis_sample_files with matching case and file-tags and version
    version = None
    sample_files = deliver_api.get_post_analysis_sample_files(
        family, sample, version, deliver_tags
    )

    # THEN we should get those matching files back
    assert sample_files


def test_get_post_analysis_sample_files_only_family_tags(analysis_family, deliver_api):

    # GIVEN a family which exist as bundle in hk
    # GIVEN corresponding houskeeper tags for those files
    family = analysis_family["internal_id"]
    sample = analysis_family["samples"][0]["internal_id"]
    deliver_tags = ["case-tag"]

    # WHEN we call get_post_analysis_sample_files with matching case and file-tags and version
    version = None
    sample_files = deliver_api.get_post_analysis_sample_files(
        family, sample, version, deliver_tags
    )

    # THEN we should get those matching files back
    assert not sample_files
