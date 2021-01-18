"""Fixtures for the upload scout api tests"""

import pytest

from tests.mocks import store_model


@pytest.fixture(name="analysis_obj")
def fixture_analysis_obj() -> store_model.Analysis:
    """Return a analysis object"""
    return store_model.Analysis()
