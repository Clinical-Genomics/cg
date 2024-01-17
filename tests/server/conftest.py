"""Test fixtures for cg/server tests"""
import os

import pytest
from flask import Flask
from flask.testing import FlaskClient
from mock import patch

from cg.constants import DataDelivery, Pipeline
from cg.server.app import create_app
from cg.store import Store
from cg.store.database import create_all_tables, drop_all_tables
from cg.store.models import Case
from tests.store_helpers import StoreHelpers

os.environ["CG_SQL_DATABASE_URI"] = "sqlite:///"
os.environ["LIMS_HOST"] = "dummy_value"
os.environ["LIMS_USERNAME"] = "dummy_value"
os.environ["LIMS_PASSWORD"] = "dummy_value"
os.environ["GOOGLE_OAUTH_CLIENT_ID"] = "dummy_value"
os.environ["GOOGLE_OAUTH_CLIENT_SECRET"] = "dummy_value"
os.environ["CG_ENABLE_ADMIN"] = "1"


@pytest.fixture
def app() -> Flask:
    app = create_app()
    create_all_tables()
    yield app
    drop_all_tables()


@pytest.fixture
def store(app: Flask) -> Store:
    from cg.server.ext import db

    yield db


@pytest.fixture
def case(store: Store, helpers: StoreHelpers) -> Case:
    case: Case = helpers.add_case(
        customer_id=1,
        data_analysis=Pipeline.MIP_DNA,
        data_delivery=DataDelivery.ANALYSIS_SCOUT,
        name="test case",
        ticket="123",
        store=store,
    )
    store.session.add(case)
    store.session.commit()
    return case


@pytest.fixture
def client(app: Flask, case: Case) -> FlaskClient:
    # Bypass authentication

    with patch.object(app, "before_request_funcs", new={}):
        yield app.test_client()
