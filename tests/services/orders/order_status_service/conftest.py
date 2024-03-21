from datetime import datetime
import pytest
from cg.apps.tb.api import TrailblazerAPI
from cg.apps.tb.dto.summary_response import AnalysisSummary

from cg.services.orders.order_status_service.order_summary_service import OrderSummaryService
from cg.store.models import Customer, Order
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


@pytest.fixture
def summary_service(trailblazer_api: TrailblazerAPI, store: Store):
    return OrderSummaryService(analysis_client=trailblazer_api, store=store)


@pytest.fixture
def order(store: Store, helpers: StoreHelpers) -> Order:
    customer: Customer = helpers.ensure_customer(store)
    order: Order = helpers.add_order(store=store, customer_id=customer.id, ticket_id="ticket_id")
    helpers.ensure_case(store=store, customer=customer, order=order)
    return order


@pytest.fixture
def analysis_summary(order: Order) -> AnalysisSummary:
    return AnalysisSummary(
        order_id=order.id,
        analysis_id=1,
        delivered=2,
        running=3,
        cancelled=4,
        failed=5,
    )

@pytest.fixture
def order_with_case_in_preparation(store: Store, helpers: StoreHelpers) -> Order:
    customer: Customer = helpers.ensure_customer(store)
    order: Order = helpers.add_order(store=store, customer_id=customer.id, ticket_id=1)
    case = helpers.ensure_case(store=store, customer=customer, order=order)
    sample = helpers.add_sample(
        store=store,
        internal_id="in_prep",
        received_at=datetime.now(),
        prepared_at=None,
        last_sequenced_at=None,
    )
    helpers.add_relationship(store=store, sample=sample, case=case)
    return order


@pytest.fixture
def order_with_case_not_received(store: Store, helpers: StoreHelpers) -> Order:
    customer: Customer = helpers.ensure_customer(store)
    order: Order = helpers.add_order(store=store, customer_id=customer.id, ticket_id=1)
    case = helpers.ensure_case(store=store, customer=customer, order=order)
    sample = helpers.add_sample(
        store=store,
        internal_id="not_received",
        received_at=None,
        prepared_at=None,
        last_sequenced_at=None,
    )
    helpers.add_relationship(store=store, sample=sample, case=case)
    return order


@pytest.fixture
def order_with_case_in_sequencing(store: Store, helpers: StoreHelpers) -> Order:
    customer: Customer = helpers.ensure_customer(store)
    order: Order = helpers.add_order(store=store, customer_id=customer.id, ticket_id=1)
    case = helpers.ensure_case(store=store, customer=customer, order=order)
    sample = helpers.add_sample(
        store=store,
        internal_id="in_sequencing",
        received_at=datetime.now(),
        prepared_at=datetime.now(),
        last_sequenced_at=None,
    )
    helpers.add_relationship(store=store, sample=sample, case=case)
    return order
