"""Fixtures for analyses rna cli tests"""
from collections import namedtuple
from typing import List
import pytest


class MockTB:
    """Trailblazer mock fixture"""

    def __init__(self):
        self._link_was_called = False

    def link(self, family: str, sample: str, analysis_type: str, files: List[str]):
        """Link files mock"""

        del family, sample, analysis_type, files

        self._link_was_called = True

    def link_was_called(self):
        """Check if link has been called"""
        return self._link_was_called

    @classmethod
    def analyses(cls, family, temp):
        """Mock TB analyses models"""

        _family = family
        _temp = temp

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

    def family(self, case_id: str):
        """Mock the family call"""

        case_obj = namedtuple('Case', 'internal_id')
        case_obj.internal_id = 'fake case'

        return case_obj


@pytest.fixture(scope='function')
def mock_store():
    """store fixture"""

    return MockStore()
