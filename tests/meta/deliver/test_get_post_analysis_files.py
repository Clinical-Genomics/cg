"""Tests for mip_dna delivery API"""


def test_get_post_analysis_files(analysis_family, deliver_api):

    ## GIVEN a family and tags
    family = analysis_family["internal_id"]
    tags = ["bam", "bam-index"]

    ## WHEN no version
    version = None
    files = deliver_api.get_post_analysis_files(family, version, tags)

    ## THEN housekeeper files should be returned
    assert files


def test_get_post_analysis_files_version(analysis_family, deliver_api):

    ## GIVEN a family and tags
    family = analysis_family["internal_id"]
    tags = ["bam", "bam-index"]

    ## WHEN version
    version = "a_date"

    files_version = deliver_api.get_post_analysis_files(family, version, tags)

    ## THEN housekeeper files should be returned
    assert files_version


def test_get_post_analysis_family_files(analysis_family, deliver_api):

    # GIVEN family exist in as bundle in hk
    # GIVEN tags exist on those files
    family = analysis_family["internal_id"]
    deliver_tags = ["gbcf"]

    # WHEN we call get_post_analysis_family_files with matching case and file-tags
    version = None
    family_files = deliver_api.get_post_analysis_family_files(
        family, version, deliver_tags
    )

    # THEN we should get those matching files back
    assert family_files
