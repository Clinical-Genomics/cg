""" Test cg.meta.upload.observations module """

import datetime

from cg.models.observations.observations_input_files import ObservationsInputFiles


class Analysis:
    """Mock Analysis object"""

    def __init__(self, case_obj):
        self.case_obj = case_obj

    @property
    def started_at(self):
        """mock started_at date"""
        return str(datetime.datetime.today())

    @property
    def family(self):
        """mock case"""
        return self.case_obj


def test_upload_observations_get_input(analysis_store, case_id, upload_observations_api):

    # GIVEN an upload_observations_api and a mocked analysis_obj
    case_obj = analysis_store.family(case_id)
    analysis_obj = Analysis(case_obj=case_obj)

    # GIVEN a observation_input_files object

    # WHEN get_input method is used given the analysis_obj as argument
    input_files = upload_observations_api.get_input(analysis_obj)

    # THEN input_files is an input_files object
    assert isinstance(input_files, ObservationsInputFiles)

    # THEN sv vcf should be set
    assert input_files.sv_vcf is not None


def test_upload_observations_get_input_wes(analysis_store, case_id, upload_observations_api_wes):

    # GIVEN an upload_observations_api and a mocked analysis_obj
    case_obj = analysis_store.family(case_id)
    analysis_obj = Analysis(case_obj=case_obj)

    # WHEN get_input method is used given the analysis_obj as argument
    input_files = upload_observations_api_wes.get_input(analysis_obj)

    # THEN input_files is an input_files object
    assert isinstance(input_files, ObservationsInputFiles)

    # THEN sv vcf should not be set
    assert input_files.sv_vcf is None


def test_upload_observations_process(analysis_store, case_id, upload_observations_api):

    # GIVEN an upload_observations_api and a mocked analysis_obj
    case_obj = analysis_store.family(case_id)
    analysis_obj = Analysis(case_obj=case_obj)

    # WHEN trying to upload observations

    upload_observations_api.process(analysis_obj)

    # THEN all samples should have gotten a loqusdb_id
    for link in analysis_obj.family.links:
        assert link.sample.loqusdb_id == "123"
