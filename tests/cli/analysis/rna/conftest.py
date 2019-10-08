"""Fixtures for analyses rna cli tests"""
from collections import namedtuple
from typing import List
import pytest


class MockTB:
    """Trailblazer mock fixture"""

    def __init__(self):
        self._link_was_called = False
        self._family = None
        self._temp = None

    def link(self, family: str, sample: str, analysis_type: str, files: List[str]):
        """Link files mock"""

        del family, sample, analysis_type, files

        self._link_was_called = True

    def link_was_called(self):
        """Check if link has been called"""
        return self._link_was_called

    def analyses(self, family, temp):
        """Mock TB analyses models"""

        self._family = family
        self._temp = temp

        class Row:
            """Mock a record representing an analysis"""

            def __init__(self):
                """Mock constructor"""

                self._first_was_called = False

            def first(self):
                """Mock that the first row doesn't exist"""

                self._first_was_called = True

                return False

            def first_was_called(self):
                """Check if first was called"""
                return self._first_was_called

        return Row()


@pytest.fixture(scope='function')
def tb_api():
    """Trailblazer API fixture"""

    return MockTB()


class MockStore():
    """We need to call the family function from the store
    without accessing the database. So here we go"""

    def __init__(self):
        """Constructor"""
        self._case_obj = None
        self._case_id = None
        self._family_was_called = False

    def family(self, case_id: str):
        """Mock the family call"""

        case_obj = namedtuple('Case', 'internal_id')
        case_obj.internal_id = 'fake case'
        self._case_id = case_id
        self._case_obj = case_obj

        self._family_was_called = True

        return case_obj

    def family_was_called(self):
        """Check if family was called"""
        return self._family_was_called


@pytest.fixture(scope='function')
def mock_store():
    """store fixture"""

    return MockStore()
