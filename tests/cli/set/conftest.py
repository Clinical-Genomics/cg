"""Fixtures for cli balsamic tests"""

import pytest

from cg.apps.lims import LimsAPI
from cg.store import Store


@pytest.fixture
def base_context(base_store: Store) -> dict:
    """context to use in cli"""
    return {"lims": MockLims(), "status": base_store}


class MockLims(LimsAPI):
    """Mock lims fixture"""

    lims = None

    def __init__(self):
        self.lims = self

    _project_name = None
    _sample_sex = None
    _sample_name = None

    def update_project(self, lims_id: str, name=None):
        """Mock lims update_project"""
        self._project_name = name

    def get_updated_project_name(self) -> str:
        """Method to test that update project was called with name parameter"""
        return self._project_name

    def update_sample(
        self,
        lims_id: str,
        sex=None,
        application: str = None,
        target_reads: int = None,
        priority=None,
        name=None,
    ):
        """Mock lims update_sample"""
        self._sample_sex = sex
        self._sample_name = name

    def get_updated_sample_sex(self) -> str:
        """Method to be used to test that update_sample was called with sex parameter"""
        return self._sample_sex

    def get_updated_sample_name(self) -> str:
        """Method to be used to test that update_sample was called with name parameter"""
        return self._sample_name
