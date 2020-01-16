""" Fixtures for microsalt CLI test """

from datetime import datetime
from pathlib import Path
import pytest

from cg.store.models import Organism, ApplicationVersion, MicrobialOrder, MicrobialSample, Customer
from cg.meta.lims.microsalt import LimsMicrosaltAPI
from cg.store import Store


@pytest.fixture(scope='function')
def queries_path(tmpdir):
    return Path(tmpdir) / 'queries'

@pytest.fixture(scope='function')
def base_context(microsalt_store, lims_api, tmpdir, queries_path):
    """ The click context for the microsalt cli """
    microsalt_api = LimsMicrosaltAPI(lims=lims_api)
    return {
        'db': microsalt_store,
        'microsalt_api': microsalt_api,
        'usalt': {
            'root': tmpdir,
            'queries_path': queries_path,
            'binary_path': '/bin/true'
        }
    }


@pytest.fixture(scope='function')
def microsalt_store(base_store: Store, microbial_sample_id) -> Store:
    """ Filled in store to be used in the tests """
    _store = base_store

    add_microbial_sample(_store, internal_id=microbial_sample_id)

    _store.commit()

    return _store


@pytest.fixture()
def microbial_sample_id():
    """ Define a microbial sample id """
    return "microbial_sample_test"


def add_microbial_sample(store, name='microbial_name_test', priority='research',
                         internal_id='microbial_sample_id') -> MicrobialSample:
    """utility function to add a sample to use in tests"""
    application_version = ensure_application_version(store)
    organism = ensure_organism(store)
    microbial_order = ensure_microbial_order(store)
    microbial_sample = store.add_microbial_sample(
        name=name,
        priority=priority,
        application_version=application_version,
        organism=organism,
        reference_genome=organism.reference_genome,
        internal_id=internal_id)

    microbial_sample.microbial_order_id = microbial_order.id
    store.add_commit(microbial_sample)
    return microbial_sample


def ensure_customer(disk_store, customer_id='cust_test') -> Customer:
    """utility function to return existing or create customer for tests"""
    customer_group = disk_store.customer_group('dummy_group')
    if not customer_group:
        customer_group = disk_store.add_customer_group('dummy_group', 'dummy group')

        customer = disk_store.add_customer(internal_id=customer_id, name="Test Customer",
                                           scout_access=False, customer_group=customer_group,
                                           invoice_address='dummy_address',
                                           invoice_reference='dummy_reference')
        disk_store.add_commit(customer)
    customer = disk_store.customer(customer_id)
    return customer


def ensure_application_version(disk_store, application_tag='dummy_tag') -> ApplicationVersion:
    """utility function to return existing or create application version for tests"""
    application = disk_store.application(tag=application_tag)
    if not application:
        application = disk_store.add_application(tag=application_tag, category='wgs',
                                                 description='dummy_description')
        disk_store.add_commit(application)

    prices = {'standard': 10, 'priority': 20, 'express': 30, 'research': 5}
    version = disk_store.application_version(application, 1)
    if not version:
        version = disk_store.add_version(application, 1, valid_from=datetime.now(),
                                         prices=prices)

        disk_store.add_commit(version)
    return version


def ensure_organism(disk_store, organism_id='organism_test',
                    reference_genome='reference_genome_test') -> Organism:
    """utility funtion to return existing or create an organism for tests"""
    organism = disk_store.add_organism(internal_id=organism_id, name=organism_id,
                                       reference_genome=reference_genome)
    disk_store.add_commit(organism)

    return organism


def ensure_microbial_order(disk_store, customer_id='cust_test',
                           internal_id='microbial_order_test',
                           name='microbial_name_test') -> MicrobialOrder:
    """utility function to return an existing or create a microbial order for tests"""
    customer = ensure_customer(disk_store, customer_id)
    order = disk_store.add_microbial_order(
        customer=customer,
        internal_id=internal_id,
        name=name,
        ordered=datetime.now())
    disk_store.add_commit(order)

    return order


class MockLims():
    """ provides a mock class overrriding relevant methods for microbial cli """

    lims = None

    def __init__(self):
        self.lims = self

    def sample(self, sample_id: str):
        """ return a mock sample """

        class LimsSample:
            """ A mock class for a sample coming from LIMS. It only needs a comment """

            def __init__(self, sample_id):
                self.sample_id = sample_id

            def get(self, key):
                return 'a comment in LimsSample'

        lims_sample = LimsSample(sample_id)

        return lims_sample

    def get_prep_method(self, sample_id: str) -> str:
        return '1337:00 Test prep method'

    def get_sequencing_method(self, sample_id: str) -> str:
        return '1338:00 Test sequencing method'


@pytest.fixture(scope='function')
def lims_api():
    """return a mocked lims"""

    _lims_api = MockLims()
    return _lims_api
