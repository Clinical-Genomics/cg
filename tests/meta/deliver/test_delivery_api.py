"""Tests for delivery API"""

from typing import List, Set
from cg.store.models import Sample, FamilySample
from cg.meta.deliver import DeliverAPI


def test_get_case_analysis_files(deliver_api: DeliverAPI, case_id: str):
    """Test to fetch case specific files for a case that exists in housekeeper"""
    # GIVEN a case which exist as bundle in hk with a version
    version_obj = deliver_api.hk_api.last_version(case_id)
    assert version_obj
    # GIVEN corresponding housekeeper tags for those files
    deliver_tags = ["case-tag"]
    # GIVEN that a case object exists in the database
    link_objs: List[FamilySample] = deliver_api.store.family_samples(case_id)
    samples: List[Sample] = [link.sample for link in link_objs]
    sample_ids: Set[str] = set([sample.internal_id for sample in samples])

    # WHEN fetching all case files from the delivery api
    bundle_latest_files = deliver_api.get_case_files_from_version(
        version_obj=version_obj, sample_ids=sample_ids
    )

    ## THEN housekeeper files should be returned
    assert bundle_latest_files


# def test_get_post_analysis_case_files_only_sample_tags(deliver_api):
#
#     # GIVEN a case which exist as bundle in hk
#     # GIVEN corresponding sample id houskeeper tags for those files
#     case = "case_id"
#     deliver_tags = ["sample-tag"]
#
#     # WHEN we call get_post_analysis_case_files with matching case and sample file-tags and version
#     version = None
#     case_files = deliver_api.get_post_analysis_case_files(case, version, deliver_tags)
#
#     # THEN we should get those matching files back
#     assert not case_files
#
#
# def test_get_post_analysis_sample_files(analysis_family, deliver_api):
#
#     # GIVEN a case which exist as bundle in hk
#     # GIVEN corresponding houskeeper tags for those files
#     case = "case_id"
#     sample = analysis_family["samples"][0]["internal_id"]
#     deliver_tags = ["sample-tag"]
#
#     # WHEN we call get_post_analysis_sample_files with matching case and file-tags and version
#     version = None
#     sample_files = deliver_api.get_post_analysis_sample_files(case, sample, version, deliver_tags)
#
#     # THEN we should get those matching files back
#     assert sample_files
#
#
# def test_get_post_analysis_sample_files_only_case_tags(analysis_family, deliver_api):
#
#     # GIVEN a case which exist as bundle in hk
#     # GIVEN corresponding houskeeper tags for those files
#     case = "case_id"
#     sample = analysis_family["samples"][0]["internal_id"]
#     deliver_tags = ["case-tag"]
#
#     # WHEN we call get_post_analysis_sample_files with matching case and file-tags and version
#     version = None
#     sample_files = deliver_api.get_post_analysis_sample_files(case, sample, version, deliver_tags)
#
#     # THEN we should get those matching files back
#     assert not sample_files
#
#
# def test_get_post_analysis_files_root_dir(deliver_api):
#
#     ## WHEN we call get_post_analysis_files_root_dir
#     root_dir = deliver_api.get_post_analysis_files_root_dir()
#
#     ## THEN we should get a path back
#     assert root_dir
