""" Fixtures for microsalt CLI test """

from datetime import datetime
from pathlib import Path
import pytest

from cg.meta.microsalt.lims import LimsMicrosaltAPI
from cg.store import Store, models


@pytest.fixture(scope="function")
def queries_path(tmpdir):
    """ The path where to store the case-configs """
    return Path(tmpdir) / "queries"


@pytest.fixture(scope="function")
def base_context(microsalt_store, lims_api, tmpdir, queries_path):
    """ The click context for the microsalt cli """
    microsalt_api = LimsMicrosaltAPI(lims=lims_api)
    return {
        "db": microsalt_store,
        "lims_microsalt_api": microsalt_api,
        "usalt": {"root": tmpdir, "queries_path": queries_path, "binary_path": "/bin/true"},
    }


@pytest.fixture(scope="function")
def microsalt_store(base_store: Store, microbial_sample_id, microbial_order_id) -> Store:
    """ Filled in store to be used in the tests """
    _store = base_store

    add_microbial_sample(
        _store, internal_id=microbial_sample_id, order_internal_id=microbial_order_id
    )

    _store.commit()

    return _store


@pytest.fixture()
def microbial_sample_id():
    """ Define a name for a microbial sample """
    return "microbial_sample_test"


@pytest.fixture()
def microbial_order_id():
    """ Define a name for a microbial order """
    return "microbial_order_test"


def add_microbial_sample(
    store,
    name="microbial_name_test",
    priority="research",
    internal_id="microbial_sample_id",
    order_internal_id="microbial_order_id",
) -> models.MicrobialSample:
    """utility function to add a sample to use in tests"""
    application_version = ensure_application_version(store)
    organism = ensure_organism(store)
    microbial_order = ensure_microbial_order(store, internal_id=order_internal_id)
    microbial_sample = store.add_microbial_sample(
        name=name,
        priority=priority,
        application_version=application_version,
        organism=organism,
        reference_genome=organism.reference_genome,
        internal_id=internal_id,
    )

    microbial_sample.microbial_order_id = microbial_order.id
    store.add_commit(microbial_sample)
    return microbial_sample


def ensure_customer(disk_store, customer_id="cust_test") -> models.Customer:
    """utility function to return existing or create customer for tests"""
    customer_group = disk_store.customer_group("dummy_group")
    if not customer_group:
        customer_group = disk_store.add_customer_group("dummy_group", "dummy group")

        customer = disk_store.add_customer(
            internal_id=customer_id,
            name="Test Customer",
            scout_access=False,
            customer_group=customer_group,
            invoice_address="dummy_address",
            invoice_reference="dummy_reference",
        )
        disk_store.add_commit(customer)
    customer = disk_store.customer(customer_id)
    return customer


def ensure_application_version(
    disk_store, application_tag="dummy_tag"
) -> models.ApplicationVersion:
    """utility function to return existing or create application version for tests"""
    application = disk_store.application(tag=application_tag)
    if not application:
        application = disk_store.add_application(
            tag=application_tag, category="wgs", description="dummy_description", percent_kth=0
        )
        disk_store.add_commit(application)

    prices = {"standard": 10, "priority": 20, "express": 30, "research": 5}
    version = disk_store.application_version(application, 1)
    if not version:
        version = disk_store.add_version(application, 1, valid_from=datetime.now(), prices=prices)

        disk_store.add_commit(version)
    return version


def ensure_organism(
    disk_store, organism_id="organism_test", reference_genome="reference_genome_test"
) -> models.Organism:
    """utility funtion to return existing or create an organism for tests"""
    organism = disk_store.add_organism(
        internal_id=organism_id, name=organism_id, reference_genome=reference_genome
    )
    disk_store.add_commit(organism)

    return organism


def ensure_microbial_order(
    disk_store,
    customer_id="cust_test",
    internal_id="microbial_order_test",
    name="microbial_name_test",
) -> models.MicrobialOrder:
    """utility function to return an existing or create a microbial order for tests"""
    customer = ensure_customer(disk_store, customer_id)
    order = disk_store.add_microbial_order(
        customer=customer,
        internal_id=internal_id,
        name=name,
        ordered=datetime.now(),
        ticket_number=123456,
    )
    disk_store.add_commit(order)

    return order


class MockLims:
    """ provides a mock class overrriding relevant methods for microbial cli """

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
                return self.sample_data.get(key, "not found")

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
