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
    return 'tests/fixtures/orderforms/1603.7.microbial.xlsx'


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


def ensure_applications(store: Store, list_of_tags: list, number_of_active_applications: int):





@pytest.fixture
def microbial_store(base_store: Store):
    """Fixture where all apptags in ordeform 1603:7, first one is inactive"""
    applications = ensure_applications(store, [''], 1)
    applications = [base_store.add_application('WGXCUSC000', 'mic', 'External WGS',
                                               sequencing_depth=0, is_external=True),
                    base_store.add_application('EXXCUSR000', 'mic', 'External WES',
                                               sequencing_depth=0, is_external=True),
                    base_store.add_application('WGSPCFC060', 'mic', 'WGS, double', sequencing_depth=30,
                                               accredited=True),
                    base_store.add_application('RMLS05R150', 'mic', 'Ready-made', sequencing_depth=0),
                    base_store.add_application('WGTPCFC030', 'mic', 'WGS trio', is_accredited=True,
                                               sequencing_depth=30, target_reads=300000000,
                                               limitations='some'),
                    base_store.add_application('METLIFR020', 'mic', 'Whole genome metagenomics',
                                               sequencing_depth=0, target_reads=40000000),
                    base_store.add_application('METNXTR020', 'mic', 'Metagenomics',
                                               sequencing_depth=0, target_reads=20000000),
                    base_store.add_application('MWRNXTR003', 'mic', 'Microbial whole genome ',
                                               sequencing_depth=0)]

    base_store.add_commit(applications)