import pytest
from cg.apps.tb.api import TrailblazerAPI
from cg.apps.tb.dto.summary_response import AnalysisSummary

from cg.services.orders.order_status_service.order_status_service import OrderStatusService
from cg.store.models import Case, Customer, Order
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


@pytest.fixture
def order_status_service(trailblazer_api: TrailblazerAPI, store: Store):
    return OrderStatusService(analysis_client=trailblazer_api, store=store)


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
