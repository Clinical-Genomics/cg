"""Fixtures for cli balsamic tests"""
from collections import namedtuple
from datetime import datetime

import pytest

from cg.apps.balsamic.fastq import BalsamicFastqHandler
from cg.apps.hk import HousekeeperAPI
from cg.meta.analysis import AnalysisAPI
from cg.store import Store


@pytest.fixture
def base_context(balsamic_store) -> dict:
    """context to use in cli"""
    return {
        'hk_api': MockHouseKeeper(),
        'db': balsamic_store,
        'analysis_api': MockAnalysis(),
        'fastq_handler': MockBalsamicFastq(),
        'balsamic': {'conda_env': 'conda_env',
                     'root': 'root',
                     'slurm': {'account': 'account', 'qos': 'qos'},
                     'singularity': 'singularity',
                     'reference_config': 'reference_config'
                     }
    }


class MockHouseKeeper(HousekeeperAPI):

    def __init__(self):
        pass

    def files(self, tags, bundle):
        return MockFile()

    def version(self, arg1: str, arg2: str):
        """Fetch version from the database."""
        return MockVersion()


class MockVersion:
    def id(self):
        return ''


class MockFile:

    def __init__(self, path=''):
        self.path = path

    def first(self):
        return MockFile()

    def full_path(self):
        return ''


class MockAnalysis(AnalysisAPI):

    def __init__(self):
        pass

    def get_latest_metadata(self, family_id):
        # Returns: dict: parsed data
        ### Define output dict
        outdata = {
            'analysis_sex': {'ADM1': 'female', 'ADM2': 'female', 'ADM3': 'female'},
            'family': 'yellowhog',
            'duplicates': {'ADM1': 13.525, 'ADM2': 12.525, 'ADM3': 14.525},
            'genome_build': 'hg19',
            'rank_model_version': '1.18',
            'mapped_reads': {'ADM1': 98.8, 'ADM2': 99.8, 'ADM3': 97.8},
            'mip_version': 'v4.0.20',
            'sample_ids': ['2018-20203', '2018-20204'],
        }

        return outdata

    def convert_panels(self, customer_id, panels):
        return ''


class MockBalsamicFastq(BalsamicFastqHandler):
    """Mock FastqHandler for analysis_api"""

    def __init__(self):
        pass


@pytest.fixture(scope='function')
def balsamic_store(base_store: Store) -> Store:

    _store = base_store
    family = add_family(_store)
    sample1 = add_sample(_store, 'sample1')
    sample2 = add_sample(_store, 'sample2')
    _store.relate_sample(family, sample1, status='unknown')
    _store.relate_sample(family, sample2, status='unknown')
    _store.commit()

    return _store


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


def add_sample(disk_store, sample_id='sample_test', gender='female'):
    """utility function to add a sample to use in tests"""
    customer = ensure_customer(disk_store)
    application_version_id = ensure_application_version(disk_store).id
    sample = disk_store.add_sample(name=sample_id, sex=gender)
    sample.application_version_id = application_version_id
    sample.customer = customer
    disk_store.add_commit(sample)
    return sample


def add_panel(disk_store, panel_id='panel_test', customer_id='cust_test'):
    """utility function to add a panel to use in tests"""
    customer = ensure_customer(disk_store, customer_id)
    panel = disk_store.add_panel(customer=customer, name=panel_id, abbrev=panel_id,
                                 version=1.0,
                                 date=datetime.now(), genes=1)
    disk_store.add_commit(panel)
    return panel


def add_family(disk_store, family_id='family_test', customer_id='cust_test'):
    """utility function to add a family to use in tests"""
    panel = add_panel(disk_store)
    customer = ensure_customer(disk_store, customer_id)
    family = disk_store.add_family(name=family_id, panels=panel.name)
    family.customer = customer
    disk_store.add_commit(family)
    return family
