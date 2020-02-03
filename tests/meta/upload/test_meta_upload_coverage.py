"""Tests for coverage meta API"""

import datetime

from cg.meta.upload.coverage import UploadCoverageApi
from cg.apps.coverage.api import ChanjoAPI


class Analysis:
    """ Mock Analysis object """

    def __init__(self, family_obj):
        self.family_obj = family_obj

    @property
    def started_at(self):
        """ mock started_at date """
        return str(datetime.datetime.today())

    @property
    def family(self):
        """ mock family """
        return self.family_obj


def test_data(coverage_upload_api, analysis_store):
    """test getting data for chanjo"""
    # GIVEN a coverage api and an analysis object
    coverage_api = coverage_upload_api
    family_name = "yellowhog"
    family_obj = analysis_store.family(family_name)
    analysis_obj = Analysis(family_obj=family_obj)

    # WHEN using the data method
    results = coverage_api.data(analysis_obj=analysis_obj)

    # THEN this returns the data needed to upload samples to chanjo
    assert results["family"] == family_name
    for sample in results["samples"]:
        assert set(sample.keys()) == set(["coverage", "sample", "sample_name"])


def test_upload(coverage_upload_api, analysis_store, mocker):

    """test uploading with chanjo"""
    # GIVEN a coverage api and a data dictionary
    coverage_api = coverage_upload_api
    family_name = "yellowhog"
    family_obj = analysis_store.family(family_name)
    analysis_obj = Analysis(family_obj=family_obj)
    data = coverage_api.data(analysis_obj=analysis_obj)

    # WHEN uploading samples in data dictionary
    coverage_api.upload(data=data, replace=True)
