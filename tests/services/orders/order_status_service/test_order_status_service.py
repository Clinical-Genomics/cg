from mock import Mock
from cg.apps.tb.dto.summary_response import AnalysisSummary
from cg.services.orders.order_status_service.order_summary_service import OrderSummaryService
from cg.services.orders.order_status_service.dto.order_summary import OrderSummary
from cg.store.models import Order


def test_get_status_summaries(
    order_status_service: OrderSummaryService, order: Order, analysis_summary: AnalysisSummary
):

    # GIVEN a store with orders

    # GIVEN that the analysis client returns analysis summaries for the order
    order_status_service.analysis_client = Mock()
    order_status_service.analysis_client.get_summaries.return_value = [analysis_summary]

    # WHEN getting status summaries
    summaries: list[OrderSummary] = order_status_service.get_summaries([order.id])

    # THEN the summaries should be returned
    assert summaries


def test_in_preparation():
    # GIVEN an order with cases in preparation

    # WHEN creating a summary for the order

    # THE summary should contain the number of cases in preparation
    pass


def test_in_sequencing():
    # GIVEN an order with cases in sequencing

    # WHEN creating a summary for the order

    # THE summary should contain the number of cases in sequencing
    pass


def test_not_rececved():
    # GIVEN an order with cases not received

    # WHEN creating a summary for the order

    # THE summary should contain the number of cases not received
    pass
