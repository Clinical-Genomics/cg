import pytest


@pytest.fixture
def rml_orderform():
    return 'tests/fixtures/orderforms/1604.5.rml.xlsx'


@pytest.fixture
def fastq_orderform():
    return 'tests/fixtures/orderforms/1508.12.fastq.xlsx'


@pytest.fixture
def scout_orderform():
    return 'tests/fixtures/orderforms/1508.12.scout.xlsx'


@pytest.fixture
def external_orderform():
    return 'tests/fixtures/orderforms/1541.6.external.xlsx'
