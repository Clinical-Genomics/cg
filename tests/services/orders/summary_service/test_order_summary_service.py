from cg.services.orders.order_summary_service.dto.order_summary import OrderSummary
from cg.services.orders.order_summary_service.order_summary_service import (
    OrderSummaryService,
)
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

    # THEN the summary should contain one case in sequencing
    assert summary.in_sequencing == 1


def test_summarize_multiple_samples_not_received(
    summary_service: OrderSummaryService, order_with_not_received_samples: Order
):
    # GIVEN an order containing a case with samples not received
    order_id: int = order_with_not_received_samples.id

    # WHEN creating a summary for the order
    summary: OrderSummary = summary_service.get_summary(order_id)

    # THEN the summary should contain one case
    assert summary.total == 1

    # THEN the summary should contain one case not received
    assert summary.not_received == 1


def test_summarize_order_with_two_cases(
    summary_service: OrderSummaryService, order_with_two_cases: Order
):
    # GIVEN an order with two cases with not received and sequenced samples
    order_id: int = order_with_two_cases.id

    # WHEN creating a summary for the order
    summary: OrderSummary = summary_service.get_summary(order_id)

    # THEN the summary should contain one case
    assert summary.total == 2

    # THEN the summary should contain one case not received
    assert summary.not_received == 2

    # THEN the summary should not contain any case in sequencing
    assert summary.in_sequencing == 0
