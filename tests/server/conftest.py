"""Test fixtures for cg/server tests"""
import os

import pytest
from cg.server.app import create_app

os.environ["CG_SQL_DATABASE_URI"] = "dummy_value"
os.environ["LIMS_HOST"] = "dummy_value"
os.environ["LIMS_USERNAME"] = "dummy_value"
os.environ["LIMS_PASSWORD"] = "dummy_value"
os.environ["GOOGLE_OAUTH_CLIENT_ID"] = "dummy_value"
os.environ["GOOGLE_OAUTH_CLIENT_SECRET"] = "dummy_value"


@pytest.fixture
def app():
    """Test fixture to use when the flask app is needed"""
    _app = create_app()
    return _app
