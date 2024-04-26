"""Test fixtures for cg/server tests"""

import os
from datetime import datetime
from typing import Generator

import pytest
from flask import Flask
from flask.testing import FlaskClient
from mock import patch

from cg.apps.tb.dto.summary_response import AnalysisSummary
from cg.apps.tb.models import TrailblazerAnalysis
from cg.constants import DataDelivery, Workflow
from cg.server.ext import db as store
from cg.store.database import create_all_tables, drop_all_tables
from cg.store.models import Case, Customer, Order
from tests.store_helpers import StoreHelpers

os.environ["CG_SQL_DATABASE_URI"] = "sqlite:///"
os.environ["LIMS_HOST"] = "dummy_value"
os.environ["LIMS_USERNAME"] = "dummy_value"
os.environ["LIMS_PASSWORD"] = "dummy_value"
os.environ["GOOGLE_OAUTH_CLIENT_ID"] = "dummy_value"
os.environ["GOOGLE_OAUTH_CLIENT_SECRET"] = "dummy_value"
os.environ["CG_ENABLE_ADMIN"] = "1"
os.environ["TRAILBLAZER_SERVICE_ACCOUNT"] = "dummy_value"
os.environ["TRAILBLAZER_SERVICE_ACCOUNT_AUTH_FILE"] = "dummy_value"
os.environ["TRAILBLAZER_HOST"] = "dummy_value"


@pytest.fixture
def app() -> Generator[Flask, None, None]:
    from cg.server.auto import app

    app.config.update({"TESTING": True})
    create_all_tables()
    yield app
    drop_all_tables()


@pytest.fixture
def order(
    helpers: StoreHelpers, customer: Customer, server_case: Case, server_case_in_same_order: Case
) -> Order:
    order: Order = helpers.add_order(
        store=store,
        customer_id=customer.id,
        ticket_id=1,
        order_date=datetime.now(),
        workflow=Workflow.MIP_DNA,
    )
    order.cases.append(server_case)
    order.cases.append(server_case_in_same_order)
    return order


@pytest.fixture
def order_another(helpers: StoreHelpers, customer_another: Customer) -> Order:
    order: Order = helpers.add_order(
        store=store, customer_id=customer_another.id, ticket_id=2, order_date=datetime.now()
    )
    return order


@pytest.fixture
def order_balsamic(helpers: StoreHelpers, customer_another: Customer) -> Order:
    order: Order = helpers.add_order(
        store=store,
        customer_id=customer_another.id,
        ticket_id=3,
        order_date=datetime.now(),
        workflow=Workflow.BALSAMIC,
    )
    return order


@pytest.fixture
def server_case(helpers: StoreHelpers) -> Case:
    case: Case = helpers.add_case(
        customer_id=1,
        data_analysis=Workflow.MIP_DNA,
        internal_id="looseygoosey",
        data_delivery=DataDelivery.ANALYSIS_SCOUT,
        name="test case",
        ticket="123",
        store=store,
    )
    return case


@pytest.fixture
def server_case_in_same_order(helpers: StoreHelpers) -> Case:
    case: Case = helpers.add_case(
        customer_id=1,
        data_analysis=Workflow.MIP_DNA,
        data_delivery=DataDelivery.ANALYSIS_SCOUT,
        internal_id="failedsnail",
        name="test case 2",
        ticket="123",
        store=store,
    )
    return case


@pytest.fixture
def trailblazer_analysis_for_server_case(server_case: Case):
    return TrailblazerAnalysis(
        case_id=server_case.internal_id,
        id=1,
        logged_at="",
        started_at="",
        completed_at="",
        out_dir="",
        config_path="",
        uploaded_at="2024-01-01",
        workflow=Workflow.MIP_DNA,
    )


@pytest.fixture
def trailblazer_analysis_for_server_case_in_same_order(server_case_in_same_order: Case):
    return TrailblazerAnalysis(
        case_id=server_case_in_same_order.internal_id,
        id=2,
        logged_at="",
        started_at="",
        completed_at="",
        out_dir="",
        config_path="",
        uploaded_at="2023-01-01",
        workflow=Workflow.MIP_DNA,
    )


@pytest.fixture
def customer(helpers: StoreHelpers) -> Customer:
    customer: Customer = helpers.ensure_customer(store=store, customer_id="test_customer")
    return customer


@pytest.fixture
def customer_another(helpers: StoreHelpers) -> Customer:
    customer: Customer = helpers.ensure_customer(store=store, customer_id="test_customer_2")
    return customer


@pytest.fixture
def non_existent_order_id() -> int:
    return 900


@pytest.fixture
def client(app: Flask) -> Generator[FlaskClient, None, None]:
    # Bypass authentication
    with patch.object(app, "before_request_funcs", new={}):
        yield app.test_client()


@pytest.fixture
def analysis_summary():
    return AnalysisSummary(
        order_id=1,
        cancelled=0,
        completed=1,
        running=0,
        delivered=1,
        failed=1,
    )
