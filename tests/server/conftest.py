"""Test fixtures for cg/server tests"""
import os
from flask import Flask
from flask.testing import FlaskClient

import pytest

from cg.server.app import create_app
from cg.store.api.core import Store

os.environ["CG_SQL_DATABASE_URI"] = "sqlite:///:memory:"
os.environ["LIMS_HOST"] = "dummy_value"
os.environ["LIMS_USERNAME"] = "dummy_value"
os.environ["LIMS_PASSWORD"] = "dummy_value"
os.environ["GOOGLE_OAUTH_CLIENT_ID"] = "dummy_value"
os.environ["GOOGLE_OAUTH_CLIENT_SECRET"] = "dummy_value"


@pytest.fixture
def app():
    """Test fixture to use when the flask app is needed"""
    return create_app()


@pytest.fixture
def client(app: Flask, store_with_multiple_cases_and_samples: Store) -> FlaskClient:
    return app.test_client()
