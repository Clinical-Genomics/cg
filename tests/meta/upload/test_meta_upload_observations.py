""" Test cg.meta.upload.observations module """

import datetime


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


def test_upload_observations_data(upload_observations_api, analysis_store):

    # GIVEN an upload_observations_api and a mocked analysis_obj
    family_obj = analysis_store.family("yellowhog")
    analysis_obj = Analysis(family_obj=family_obj)

    # WHEN data method is used given the analysis_obj as argument
    data = upload_observations_api.data(analysis_obj)

    # THEN data is a dictionary with keys (family, vcf, sv_vcf, snv_gbcf, and pedigree)
    assert set(data.keys()) == {"family", "vcf", "sv_vcf", "snv_gbcf", "pedigree"}


def test_upload_observations_process(upload_observations_api, analysis_store):

    # GIVEN an upload_observations_api and a mocked analysis_obj
    family_obj = analysis_store.family("yellowhog")
    analysis_obj = Analysis(family_obj=family_obj)

    # WHEN trying to upload observations

    upload_observations_api.process(analysis_obj)

    # THEN all samples will have gotten a loqusdb_id
    for link in analysis_obj.family.links:
        assert link.sample.loqusdb_id == "123"
