"""Pytest fixtures for testing the store/api"""

import pytest
from cg.store import Store
from tests.store.api.test_store_import_func import add_applications


@pytest.fixture
def application_versions_file():
    """"application version import file"""
    return 'tests/fixtures/store/api/application_versions.xlsx'


@pytest.fixture
def applications_file():
    """"application import file"""
    return 'tests/fixtures/store/api/applications.xlsx'


@pytest.fixture
def balsamic_orderform():
    """Orderform fixture for Balsamic samples"""
    return 'tests/fixtures/orderforms/1508.17.balsamic.xlsx'


@pytest.fixture
def external_orderform():
    """Orderform fixture for external samples"""
    return 'tests/fixtures/orderforms/1541.6.external.xlsx'


@pytest.fixture
def fastq_orderform():
    """Orderform fixture for fastq samples"""
    return 'tests/fixtures/orderforms/1508.17.fastq.xlsx'


@pytest.fixture
def metagenome_orderform():
    """Orderform fixture for metagenome samples"""
    return 'tests/fixtures/orderforms/1605.6.metagenome.xlsx'


@pytest.fixture
def microbial_orderform():
    """Orderform fixture for microbial samples"""
    return 'tests/fixtures/orderforms/1603.8.microbial.xlsx'


@pytest.fixture
def mip_orderform():
    """Orderform fixture for MIP samples"""
    return 'tests/fixtures/orderforms/1508.17.mip.xlsx'


@pytest.fixture
def mip_balsamic_orderform():
    """Orderform fixture for MIP and Balsamic samples"""
    return 'tests/fixtures/orderforms/1508.17.mip_balsamic.xlsx'


@pytest.fixture
def rml_orderform():
    """Orderform fixture for RML samples"""
    return 'tests/fixtures/orderforms/1604.9.rml.xlsx'
