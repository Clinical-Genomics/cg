from http import HTTPStatus

import mock.mock
from flask.testing import FlaskClient

from cg.apps.tb import TrailblazerAPI
from cg.apps.tb.dto.summary_response import AnalysisSummary
from cg.store.models import Order


def test_order_endpoint(
    client: FlaskClient, order: Order, order_another: Order, analysis_summary: AnalysisSummary
):
    """Tests that the order endpoint returns the order with matching id"""
    # GIVEN a store with two orders
    order_id_to_fetch: int = order.id

    # WHEN a request is made to get a specific order
    endpoint: str = f"/api/v1/orders/{order_id_to_fetch}"
    with mock.patch.object(TrailblazerAPI, "get_summaries", return_value=[analysis_summary]):
        response = client.get(endpoint)

    # THEN the response should be successful
    assert response.status_code == HTTPStatus.OK

    # THEN the response should only contain the specified order
    assert response.json


def test_order_endpoint_not_found(
    client: FlaskClient, order: Order, order_another: Order, non_existent_order_id: int
):
    """Tests that the order endpoint returns the order with matching id"""
    # GIVEN a store with two orders

    # WHEN a request is made to get a non-existent order
    endpoint: str = f"/api/v1/orders/{non_existent_order_id}"
    response = client.get(endpoint)

    # THEN the response should be unsuccessful
    assert response.status_code == HTTPStatus.NOT_FOUND
