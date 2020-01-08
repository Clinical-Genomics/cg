"""Fixtures for testing apps"""

import pytest
import requests


@pytest.fixture
def response():
    """Mock a requests.response object"""

    class MockResponse(requests.Response):
        """Mock requests.response class"""

        def __init__(self):
            pass

        @property
        def ok(self):
            """Mock ok"""
            return False

        @property
        def text(self):
            """Mock text"""
            return "response text"

        @property
        def reason(self):
            """Mock reason"""
            return "response reason"

    return MockResponse()
