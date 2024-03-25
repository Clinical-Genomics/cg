from cg.services.orders.order_status_service.order_summary_service import OrderSummaryService
from cg.services.orders.order_status_service.dto.order_summary import OrderSummary
from cg.store.models import Order


def test_get_status_summaries(summary_service: OrderSummaryService, order: Order):

    # GIVEN a store with orders

    # WHEN getting status summaries
    summaries: list[OrderSummary] = summary_service.get_summaries([order.id])

    # THEN the summaries should be returned
    assert summaries


def test_not_received(summary_service: OrderSummaryService, order_with_cases: Order):
    # GIVEN an order with one case that has not been received
    order_id: int = order_with_cases.id

    # WHEN creating a summary for the order
    summary: OrderSummary = summary_service.get_summary(order_id)

    # THEN the summary should contain one case not received
    assert summary.not_received == 1


def test_in_preparation(summary_service: OrderSummaryService, order_with_cases: Order):
    # GIVEN an order with one case in preparation
    order_id: int = order_with_cases.id

    # WHEN creating a summary for the order
    summary: OrderSummary = summary_service.get_summary(order_id)

    # THEN the summary should contain one case in preparation
    assert summary.in_lab_preparation == 1


def test_in_sequencing(summary_service: OrderSummaryService, order_with_cases: Order):
    # GIVEN an order with one case in sequencing
    order_id: int = order_with_cases.id

    # WHEN creating a summary for the order
    summary: OrderSummary = summary_service.get_summary(order_id)

    # THE summary should contain one case in sequencing
    assert summary.in_sequencing == 1
