from datetime import datetime

import pytest
from mock import Mock

from cg.apps.tb.dto.summary_response import AnalysisSummary
from cg.services.orders.order_summary_service.order_summary_service import (
    OrderSummaryService,
)
from cg.store.models import Case, Customer, Order, Sample
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


@pytest.fixture
def summary_service(store: Store, order: Order, analysis_summary: AnalysisSummary):
    service = OrderSummaryService(analysis_client=Mock(), store=store)
    service.analysis_client.get_summaries.return_value = [analysis_summary]
    return service


@pytest.fixture
def order(store: Store, helpers: StoreHelpers) -> Order:
    customer: Customer = helpers.ensure_customer(store)
    order: Order = helpers.add_order(store=store, customer_id=customer.id, ticket_id="ticket_id")
    return order


@pytest.fixture
def sample_not_received(store: Store, helpers: StoreHelpers) -> Sample:
    return helpers.add_sample(
        store=store,
        internal_id="not_received",
    )


@pytest.fixture
def another_sample_not_received(store: Store, helpers: StoreHelpers) -> Sample:
    return helpers.add_sample(
        store=store,
        internal_id="another_not_received",
    )


@pytest.fixture
def sample_in_preparation(store: Store, helpers: StoreHelpers) -> Sample:
    return helpers.add_sample(
        store=store,
        internal_id="in_prep",
        received_at=datetime.now(),
    )


@pytest.fixture
def sample_in_sequencing(store: Store, helpers: StoreHelpers) -> Sample:
    return helpers.add_sample(
        store=store,
        internal_id="in_sequencing",
        received_at=datetime.now(),
        prepared_at=datetime.now(),
    )


@pytest.fixture
def order_with_cases(
    store: Store,
    helpers: StoreHelpers,
    order: Order,
    sample_in_preparation: Sample,
    sample_in_sequencing: Sample,
    sample_not_received: Sample,
) -> Order:
    case_not_received: Case = helpers.ensure_case(
        store=store,
        customer=order.customer,
        order=order,
        case_name="case_not_received",
        case_id="case_not_received",
    )
    case_in_preparation: Case = helpers.ensure_case(
        store=store,
        customer=order.customer,
        order=order,
        case_name="case_in_preparation",
        case_id="case_in_preparation",
    )
    case_in_sequencing: Case = helpers.ensure_case(
        store=store,
        customer=order.customer,
        order=order,
        case_name="case_in_sequencing",
        case_id="case_in_sequencing",
    )
    # Add samples to case that has not been received
    helpers.add_relationship(store=store, sample=sample_not_received, case=case_not_received)
    helpers.add_relationship(store=store, sample=sample_in_preparation, case=case_not_received)
    helpers.add_relationship(store=store, sample=sample_in_sequencing, case=case_not_received)

    # Add samples to case that is in preparation
    helpers.add_relationship(store=store, sample=sample_in_preparation, case=case_in_preparation)
    helpers.add_relationship(store=store, sample=sample_in_sequencing, case=case_in_preparation)

    # Add samples to case that is in sequencing
    helpers.add_relationship(store=store, sample=sample_in_sequencing, case=case_in_sequencing)
    return order


@pytest.fixture
def order_with_not_received_samples(
    store: Store,
    helpers: StoreHelpers,
    order: Order,
    sample_not_received: Sample,
    another_sample_not_received: Sample,
) -> Order:
    case_not_received: Case = helpers.ensure_case(
        store=store,
        customer=order.customer,
        order=order,
        case_name="case_not_received",
        case_id="case_not_received",
    )
    # Add samples to case that has not been received
    helpers.add_relationship(store=store, sample=sample_not_received, case=case_not_received)
    helpers.add_relationship(
        store=store, sample=another_sample_not_received, case=case_not_received
    )
    return order


@pytest.fixture
def order_with_two_cases(
    order: Order,
    sample_not_received: Sample,
    store: Store,
    helpers: StoreHelpers,
) -> Order:
    case_1: Case = helpers.ensure_case(
        store=store,
        customer=order.customer,
        order=order,
        case_name="case_not_received_1",
        case_id="case_not_received_1",
    )
    case_2: Case = helpers.ensure_case(
        store=store,
        customer=order.customer,
        order=order,
        case_name="case_not_received_2",
        case_id="case_not_received_2",
    )
    # Add samples
    helpers.add_relationship(store=store, sample=sample_not_received, case=case_1)
    helpers.add_relationship(store=store, sample=sample_not_received, case=case_2)
    return order
