"""Fixtures for analyses rna cli tests"""
from collections import namedtuple
import pytest


class MockTB:
    """Trailblazer mock fixture"""

    def __init__(self):
        self._link_was_called = False
        self._mark_analyses_deleted_called = False
        self._add_pending_was_called = False
        self._add_pending_analysis_was_called = False
        self._family = None
        self._temp = None
        self._case_id = None
        self._email = None

    def analyses(self, family, temp):
        """Mock TB analyses models"""

        self._family = family
        self._temp = temp

        class Row:
            """Mock a record representing an analysis"""

            def __init__(self):
                """We need to initialize _first_was_called
                so that we can set it in `first()` and retrieve
                it in `first_was_called()`. This way we can easily
                run the invoking code and make sure the function was
                called.
                """

                self._first_was_called = False

            def first(self):
                """Mock that the first row doesn't exist"""
                self._first_was_called = True

            def first_was_called(self):
                """Check if first was called"""
                return self._first_was_called

        return Row()

    def mark_analyses_deleted(self, case_id: str):
        """Mock this function"""
        self._case_id = case_id
        self._mark_analyses_deleted_called = True

    def add_pending(self, case_id: str, email: str):
        """Mock this function"""
        self._case_id = case_id
        self._email = email
        self._add_pending_was_called = True

    def add_pending_analysis(self, case_id: str, email: str):
        """Mock adding a pending analyses"""
        self._case_id = case_id
        self._email = email
        self._add_pending_analysis_was_called = True

    def mark_analyses_deleted_called(self):
        """check if mark_analyses_deleted was called"""
        return self._mark_analyses_deleted_called

    def add_pending_was_called(self):
        """check if add_pending was called"""
        return self._add_pending_was_called


@pytest.fixture(scope="function")
def tb_api():
    """Trailblazer API fixture"""

    return MockTB()


class MockStore:
    """We need to call the family function from the store
    without accessing the database. So here we go"""

    def __init__(self):
        """Constructor"""
        self._case_obj = None
        self._case_id = None
        self._family_was_called = False

    def family(self, case_id: str):
        """Mock the family call"""

        case_obj = namedtuple("Case", "internal_id")
        case_obj.internal_id = "fake case"
        self._case_id = case_id
        self._case_obj = case_obj

        self._family_was_called = True

        return case_obj

    def family_was_called(self):
        """Check if family was called"""
        return self._family_was_called


@pytest.fixture(scope="function")
def mock_store():
    """store fixture"""

    return MockStore()
