from mock import Mock
from cg.apps.tb.dto.summary_response import AnalysisSummary
from cg.services.orders.order_status_service.order_status_service import OrderStatusService
from cg.services.orders.order_status_service.dto.order_status_summary import OrderSummary
from cg.store.models import Order


def test_get_status_summaries(
    order_status_service: OrderStatusService, order: Order, analysis_summary: AnalysisSummary
):

    # GIVEN a store with orders

    # GIVEN that the analysis client returns analysis summaries for the order
    order_status_service.analysis_client = Mock()
    order_status_service.analysis_client.get_summaries.return_value = [analysis_summary]

    # WHEN getting status summaries
    summaries: list[OrderSummary] = order_status_service.get_status_summaries([order.id])

    # THEN the summaries should be returned
    assert summaries
