""" Fixtures for microsalt CLI test """

from pathlib import Path

import pytest
from cg.apps.hermes.hermes_api import HermesApi
from cg.meta.workflow.microsalt import MicrosaltAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.store import Store
from tests.store_helpers import StoreHelpers


class MockLims:
    """ provides a mock class overriding relevant methods for microbial cli """

    def __init__(self):
        self.lims = self
        self.sample_id = None
        self.lims_sample = None

    def sample(self, sample_id: str):
        """ return a mock sample """

        class LimsSample:
            """ A mock class for a sample coming from LIMS. It only needs a comment """

            def __init__(self, sample_id):
                self.sample_id = sample_id
                self.sample_data = {"comment": "a comment in LimsSample"}

            def get(self, key):
                """ only here to get the sample.get('comment') """
                return self.sample_data.get(key, "")

        # haha, it's a factory!
        if not self.lims_sample:
            self.lims_sample = LimsSample(sample_id)

        return self.lims_sample

    def get_prep_method(self, sample_id: str) -> str:
        """ Return a prep method name. Needs to be in format 'dddd:dd string' """
        self.sample_id = sample_id
        return "1337:00 Test prep method"

    def get_sequencing_method(self, sample_id: str) -> str:
        """ Return a sequencing method name. Needs to be in format 'dddd:dd string' """
        self.sample_id = sample_id
        return "1338:00 Test sequencing method"

    def get_sample_project(self, sample_id: str) -> str:
        return self.sample(sample_id).get("project").get("id")

    def get_sample_comment(self, sample_id: str) -> str:
        return self.sample(sample_id).get("comment")


class LimsFactory:
    """ Just give one LIMS """

    single_lims = None

    @classmethod
    def produce(cls):
        """ Produce me one LIMS """
        if not cls.single_lims:
            cls.single_lims = MockLims()

        return cls.single_lims


@pytest.fixture(scope="function")
def lims_api():
    """return a mocked lims"""
    return LimsFactory.produce()


@pytest.fixture(scope="function")
def base_context(cg_context: CGConfig, helpers: StoreHelpers, lims_api):
    """ The click context for the microsalt cli """
    helpers.add_microbial_sample(cg_context.status_db)
    cg_context.lims_api_ = lims_api
    cg_context.meta_apis["analysis_api"] = MicrosaltAnalysisAPI(cg_context)
    return cg_context


@pytest.fixture(name="microbial_sample_id")
def fixture_microbial_sample_id():
    """ Define a name for a microbial sample """
    return "microbial_sample_id"


@pytest.fixture(name="microbial_sample_name")
def fixture_microbial_sample_name():
    """ Define a name for a microbial sample """
    return "microbial_sample_name"


@pytest.fixture(name="microbial_ticket")
def fixture_microbial_ticket():
    """ Define a ticket for a microbial order """
    return "123456"


@pytest.fixture(scope="function")
def invalid_ticket_number() -> str:
    return "1234560000"
