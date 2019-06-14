"""Pytest fixtures for testing the store/api"""

import pytest


@pytest.fixture
def application_versions_file():
    """"application version import file"""
    return 'tests/fixtures/store/api/application_versions.xlsx'


@pytest.fixture
def applications_file():
    """"application import file"""
    return 'tests/fixtures/store/api/applications.xlsx'


@pytest.fixture
def microbial_orderform():
    """Orderform fixture for microbial samples"""
    return 'tests/fixtures/orderforms/1603.8.microbial.xlsx'
