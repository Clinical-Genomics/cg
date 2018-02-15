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
