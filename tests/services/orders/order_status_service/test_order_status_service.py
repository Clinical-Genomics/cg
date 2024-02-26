from cg.apps.tb.dto.summary_response import AnalysisSummary
from cg.services.orders.order_status_service.order_status_service import OrderStatusService
from cg.store.models import Order


def test_get_status_summaries(
    order_status_service: OrderStatusService, order: Order, analysis_summary: AnalysisSummary
):

    # GIVEN a store with orders

    # GIVEN that the analysis client returns analysis summaries for the order
    order_status_service.analysis_client.get_summaries.return_value = [analysis_summary]

    # WHEN getting status summaries
    result = order_status_service.get_status_summaries([order.id])

    # THEN the result should be a list of order status summaries
    assert result == [OrderStatusSummary(), OrderStatusSummary()]

    # THEN the store should have been called with the order ids
    order_status_service.store.get_orders_by_ids.assert_called_once_with(order_ids)

    # THEN the analysis client should have been called with the order ids
    order_status_service.analysis_client.get_summaries.assert_called_once_with(order_ids)
