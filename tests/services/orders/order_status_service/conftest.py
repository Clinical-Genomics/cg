from datetime import datetime
from mock import Mock
import pytest
from cg.apps.tb.api import TrailblazerAPI
from cg.apps.tb.dto.summary_response import AnalysisSummary

from cg.services.orders.order_status_service.order_summary_service import OrderSummaryService
from cg.store.models import Customer, Order, Sample
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


@pytest.fixture
def summary_service(trailblazer_api: TrailblazerAPI, store: Store, order: Order):
    service = OrderSummaryService(analysis_client=trailblazer_api, store=store)
    service.analysis_client = Mock()
    service.analysis_client.get_summaries.return_value = [AnalysisSummary(order_id=order.id)]
    return service


@pytest.fixture
def order(store: Store, helpers: StoreHelpers) -> Order:
    customer: Customer = helpers.ensure_customer(store)
    order: Order = helpers.add_order(store=store, customer_id=customer.id, ticket_id="ticket_id")
    helpers.ensure_case(store=store, customer=customer, order=order)
    return order


@pytest.fixture
def sample_not_received(store: Store, helpers: StoreHelpers) -> Sample:
    return helpers.add_sample(
        store=store,
        internal_id="not_received",
        received_at=None,
        prepared_at=None,
        last_sequenced_at=None,
    )


@pytest.fixture
def sample_in_preparation(store: Store, helpers: StoreHelpers) -> Sample:
    return helpers.add_sample(
        store=store,
        internal_id="in_prep",
        received_at=datetime.now(),
        prepared_at=None,
        last_sequenced_at=None,
    )


@pytest.fixture
def sample_in_sequencing(store: Store, helpers: StoreHelpers) -> Sample:
    return helpers.add_sample(
        store=store,
        internal_id="in_sequencing",
        received_at=datetime.now(),
        prepared_at=datetime.now(),
        last_sequenced_at=None,
    )


@pytest.fixture
def order_with_cases_in_lab(
    store: Store,
    helpers: StoreHelpers,
    order: Order,
    sample_in_preparation: Sample,
    sample_in_sequencing: Sample,
    sample_not_received: Sample,
) -> Order:
    case = helpers.ensure_case(store=store, customer=order.customer, order=order)
    helpers.add_relationship(store=store, sample=sample_in_preparation, case=case)
    helpers.add_relationship(store=store, sample=sample_in_sequencing, case=case)
    helpers.add_relationship(store=store, sample=sample_not_received, case=case)
    return order
