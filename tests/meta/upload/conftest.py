import json

import pytest

from cg.meta.upload.scoutapi import UploadScoutAPI
from cg.apps import hk, scoutapi, madeline
from cg.store import models, Store
from cg.meta.analysis import AnalysisAPI
import datetime

from cg.store import Store


class MockLogger:
    last_warning = None
    warnings = []

    def warning(self, text: str):
        self.last_warning = text
        self.warnings.append(text)

    def get_last_warning(self) -> str:
        return self.last_warning

    def get_warnings(self) -> list:
        return self.warnings


class MockDB(Store):
    _family_samples_returns_no_reads = False
    _application_accreditation = None

    def __init__(self, store):
        self.store = store

    def family_samples(self, family_id: str):

        family_samples = self.store.family_samples(family_id)

        if self._family_samples_returns_no_reads:
            for family_sample in family_samples:
                family_sample.sample.reads = None

        return family_samples

    def application(self, tag: str):
        """Fetch an application from the store."""
        application = self.store.application(tag=tag)

        if self._application_accreditation is not None:
            application.is_accredited = self._application_accreditation

        return application


class MockUploadScout(UploadScoutAPI):

    def __init__(self, status_api: Store, hk_api: hk.HousekeeperAPI,
                 scout_api: scoutapi.ScoutAPI, madeline_exe: str):

        self.status = status_api
        self.housekeeper = hk_api
        self.scout = scout_api
        self.madeline_exe = madeline_exe


class MockHK:
    pass


class MockCase(object):
    def __init__(self, case_id):
        self.case_id = case_id

    delivery_report = ''

    def save(self):
        pass


class MockScout:
    _cases = {}

    def case(self, institute_id, display_name):
        return self._get_MockCase(institute_id=institute_id, display_name=display_name)

    def _get_MockCase(self, institute_id, display_name):
        case_id = institute_id + display_name
        if case_id not in self._cases:
            self._cases[case_id] = MockCase(case_id)

        return self._cases[case_id]


@pytest.fixture(scope='function')
def upload_scout_api(analysis_store):
    status = MockDB(analysis_store)
    hk_api = MockHK()
    scout_api = MockScout()
    madeline = 'mockMadde'
    _scout_api = MockUploadScout(status_api=status, hk_api=hk_api, scout_api=scout_api,
                                  madeline_exe=madeline)
    return _scout_api
