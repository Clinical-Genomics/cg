import json

import pytest

from cg.meta.report.api import ReportAPI
import datetime


class MockLims():

    def get_prepmethod(self, lims_id: str) -> str:
        pass

    def get_sequencingmethod(self, lims_id: str) -> str:
        pass

    def get_deliverymethod(self, lims_id: str) -> str:
        pass

    def get_processing_time(self, lims_id: str) -> str:
        return datetime.datetime.today() - datetime.datetime.today()


@pytest.fixture(scope='function')
def report_api(base_store):
    lims = MockLims()
    _report_api = ReportAPI(lims_api=lims, db=base_store)
    return _report_api


@pytest.fixture
def case_data_path():
    _in_data_path = 'tests/fixtures/cli/report/case_data.json'
    return _in_data_path


@pytest.fixture
def case_data(case_data_path):
    return json.load(open(case_data_path))


@pytest.fixture
def report_data():
    return json.load(open('tests/fixtures/cli/report/report_data.json'))
