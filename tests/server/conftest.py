"""Test fixtures for cg/server tests"""
import os
from flask import Flask
from flask.testing import FlaskClient
from mock import patch

import pytest

from cg.server.app import create_app
from cg.store.api.core import Store

os.environ["CG_SQL_DATABASE_URI"] = "sqlite:///"
os.environ["LIMS_HOST"] = "dummy_value"
os.environ["LIMS_USERNAME"] = "dummy_value"
os.environ["LIMS_PASSWORD"] = "dummy_value"
os.environ["GOOGLE_OAUTH_CLIENT_ID"] = "dummy_value"
os.environ["GOOGLE_OAUTH_CLIENT_SECRET"] = "dummy_value"
os.environ["CG_ENABLE_ADMIN"] = "1"


@pytest.fixture
def app():
    yield create_app()


@pytest.fixture
def client(app: Flask, store_with_multiple_cases_and_samples: Store) -> FlaskClient:
    # Bypass authentication
    with patch.object(app, "before_request_funcs", new={}):
        yield app.test_client()
