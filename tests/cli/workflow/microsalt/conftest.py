""" Fixtures for microsalt CLI test """

from pathlib import Path

import pytest

from cg.meta.microsalt.lims import LimsMicrosaltAPI
from cg.meta.workflow.microsalt import AnalysisAPI
from cg.store import Store


@pytest.fixture(scope="function")
def queries_path(tmpdir):
    """ The path where to store the case-configs """
    return Path(tmpdir) / "queries"


@pytest.fixture(scope="function")
def base_context(microsalt_store, lims_api, tmpdir, queries_path, housekeeper_api):
    """ The click context for the microsalt cli """
    lims_microsalt_api = LimsMicrosaltAPI(lims=lims_api)
    return {
        "db": microsalt_store,
        "api": AnalysisAPI(db=microsalt_store, hk_api=housekeeper_api, lims_api=lims_api),
        "lims_microsalt_api": lims_microsalt_api,
        "usalt": {
            "root": tmpdir,
            "queries_path": queries_path,
            "binary_path": "/bin/true",
        },
    }


@pytest.fixture(scope="function")
def microsalt_store(base_store: Store, microbial_sample_id, microbial_ticket, helpers) -> Store:
    """ Filled in store to be used in the tests """
    _store = base_store
    helpers.add_microbial_sample_and_order(
        _store, ticket=microbial_ticket, sample_id=microbial_sample_id
    )

    _store.commit()

    return _store


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
                self.sample_data = {"comment": "a comment in LimsSample", "": ""}

            def get(self, key):
                """ only here to get the sample.get('comment') """
                return self.sample_data.get(key, "not found")

        # haha, it's a factory!
        if not self.lims_sample:
            self.lims_sample = LimsSample(sample_id)

        return self.lims_sample

    def get_sample_organism(self, lims_id: str) -> str:
        return self.sample(lims_id).get("organism")

    def get_sample_reference_genome(self, lims_id: str) -> str:
        return self.sample(lims_id).get("reference_genome")

    def get_prep_method(self, sample_id: str) -> str:
        """ Return a prep method name. Needs to be in format 'dddd:dd string' """
        self.sample_id = sample_id
        return "1337:00 Test prep method"

    def get_sequencing_method(self, sample_id: str) -> str:
        """ Return a sequencing method name. Needs to be in format 'dddd:dd string' """
        self.sample_id = sample_id
        return "1338:00 Test sequencing method"


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

    _lims_api = LimsFactory.produce()
    return _lims_api
