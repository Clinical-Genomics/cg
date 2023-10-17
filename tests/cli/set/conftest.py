"""Fixtures for cli balsamic tests"""

import pytest

from cg.apps.lims import LimsAPI
from cg.models.cg_config import CGConfig


@pytest.fixture
def base_context(cg_context: CGConfig) -> CGConfig:
    """context to use in cli"""
    cg_context.lims_api_ = MockLims()
    return cg_context


class MockLims(LimsAPI):
    """Mock lims fixture"""

    lims = None

    def __init__(self):
        self.lims = self

    _project_name = None
    _updated_key = None
    _updated_value = None

    def update_project(self, lims_id: str, name=None):
        """Mock lims update_project"""
        self._project_name = name

    def get_updated_project_name(self) -> str:
        """Method to help test that update project was called with name parameter"""
        return self._project_name

    def update_sample(self, lims_id: str, **kwargs):
        """Mock lims update_sample"""
        for key, value in kwargs.items():
            # n.b. only works when len(kwargs)==1
            self._updated_key = key
            self._updated_value = value

    def get_updated_sample_key(self) -> str:
        """Method to help test that update sample was called with key parameter"""
        return self._updated_key

    def get_updated_sample_value(self) -> str:
        """Method to help test that update sample was called with value"""
        return self._updated_value
