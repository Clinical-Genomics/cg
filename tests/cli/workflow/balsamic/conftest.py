"""Fixtures for cli balsamic tests"""
from datetime import datetime

import pytest
from cg.apps.balsamic.fastq import BalsamicFastqHandler
from cg.apps.hk import HousekeeperAPI
from cg.meta.workflow.balsamic import AnalysisAPI
from cg.store import Store, models


@pytest.fixture
def base_context(balsamic_store) -> dict:
    """context to use in cli"""
    return {
        'hk_api': MockHouseKeeper(),
        'db': balsamic_store,
        'analysis_api': MockAnalysis,
        'fastq_handler': MockBalsamicFastq,
        'gzipper': MockGzip(),
        'bed_path': 'bed_path',
        'balsamic': {'conda_env': 'conda_env',
                     'root': 'root',
                     'slurm': {'account': 'account', 'qos': 'qos'},
                     'singularity': 'singularity',
                     'reference_config': 'reference_config',
                     }
    }


class MockHouseKeeper(HousekeeperAPI):
    """Mock HousekeeperAPI"""
    def __init__(self):
        pass

    def get_files(self, bundle: str, tags: list, version: int = None):
        """Mock get_files of HousekeeperAPI"""
        del tags, bundle, version
        return [MockFile()]


class MockFile:
    """Mock File"""
    def __init__(self, path=''):
        self.path = path
        self.full_path = path


class MockGzip:
    """Mock gzip"""
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self

    def open(self, full_path):
        """Mock the gzip open function"""
        del full_path
        return self

    def readline(self):
        """Mock the gzip readline function"""
        return MockLine()


class MockLine:
    """Mock line from readline"""
    def decode(self):
        """Mock the gzip.readline.decode function"""
        return 'headerline'


class MockAnalysis(AnalysisAPI):
    """Mock AnalysisAPI"""

    @staticmethod
    def fastq_header(line):
        """Mock AnalysisAPI.fastq_header"""
        del line

        _header = {
            'lane': '1',
            'flowcell': 'ABC123',
            'readnumber': '1',
        }

        return _header


class MockBalsamicFastq(BalsamicFastqHandler):
    """Mock FastqHandler for analysis_api"""

    def __init__(self):
        pass


@pytest.fixture(scope='function')
def balsamic_store(base_store: Store) -> Store:
    """real store to be used in tests"""
    _store = base_store

    case = add_family(_store, 'balsamic_case')
    tumour_sample = add_sample(_store, 'tumour_sample', is_tumour=True)
    normal_sample = add_sample(_store, 'normal_sample', is_tumour=False)
    _store.relate_sample(case, tumour_sample, status='unknown')
    _store.relate_sample(case, normal_sample, status='unknown')

    case = add_family(_store, 'mip_case')
    normal_sample = add_sample(_store, 'normal_sample', is_tumour=False, data_analysis='mip')
    _store.relate_sample(case, normal_sample, status='unknown')

    _store.commit()

    return _store


@pytest.fixture(scope='function')
def balsamic_case(analysis_store) -> models.Family:
    """case with balsamic data_type"""
    return analysis_store.find_family(ensure_customer(analysis_store), 'balsamic_case')


@pytest.fixture(scope='function')
def mip_case(analysis_store) -> models.Family:
    """case with balsamic data_type"""
    return analysis_store.find_family(ensure_customer(analysis_store), 'mip_case')


def ensure_application_version(disk_store, application_tag='dummy_tag'):
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


def ensure_bed_version(disk_store, bed_name='dummy_bed'):
    """utility function to return existing or create bed version for tests"""
    bed = disk_store.bed(name=bed_name)
    if not bed:
        bed = disk_store.add_bed(name=bed_name)
        disk_store.add_commit(bed)

    version = disk_store.latest_bed_version(bed_name)
    if not version:
        version = disk_store.add_bed_version(bed, 1, 'dummy_filename')
        disk_store.add_commit(version)
    return version


def ensure_customer(disk_store, customer_id='cust_test'):
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


def add_sample(store, sample_id='sample_test', gender='female', is_tumour=False,
               data_analysis='balsamic'):
    """utility function to add a sample to use in tests"""
    customer = ensure_customer(store)
    application_version_id = ensure_application_version(store).id
    bed_version_id = ensure_bed_version(store).id
    sample = store.add_sample(name=sample_id, sex=gender, tumour=is_tumour,
                              sequenced_at=datetime.now(),
                              data_analysis=data_analysis)

    sample.application_version_id = application_version_id
    sample.bed_version_id = bed_version_id
    sample.customer = customer
    store.add_commit(sample)
    return sample


def ensure_panel(disk_store, panel_id='panel_test', customer_id='cust_test'):
    """utility function to add a panel to use in tests"""
    customer = ensure_customer(disk_store, customer_id)
    panel = disk_store.panel(panel_id)
    if not panel:
        panel = disk_store.add_panel(customer=customer, name=panel_id, abbrev=panel_id,
                                     version=1.0,
                                     date=datetime.now(), genes=1)
        disk_store.add_commit(panel)
    return panel


def add_family(disk_store, family_id='family_test', customer_id='cust_test'):
    """utility function to add a family to use in tests"""
    panel = ensure_panel(disk_store)
    customer = ensure_customer(disk_store, customer_id)
    family = disk_store.add_family(name=family_id, panels=panel.name)
    family.customer = customer
    disk_store.add_commit(family)
    return family
