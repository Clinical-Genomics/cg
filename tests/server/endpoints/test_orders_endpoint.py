from http import HTTPStatus

import pytest
from flask.testing import FlaskClient

from cg.constants import Workflow
from cg.services.orders.utils import create_order_response
from cg.store.models import Order


@pytest.mark.parametrize(
    "limit, workflow, expected_orders",
    [
        (None, Workflow.MIP_DNA, 2),
        (1, Workflow.MIP_DNA, 1),
        (2, Workflow.MIP_DNA, 2),
        (None, Workflow.BALSAMIC, 1),
        (None, Workflow.FLUFFY, 0),
        (None, None, 3),
    ],
)
def test_orders_endpoint(
    client: FlaskClient,
    order: Order,
    order_another: Order,
    order_balsamic: Order,
    limit: int | None,
    workflow: str,
    expected_orders: int,
):
    """Tests that orders are returned from the orders endpoint"""
    # GIVEN a store with three orders, two of which are MIP-DNA and the last is BALSAMIC

    # WHEN a request is made to get all orders
    endpoint: str = "/api/v1/orders"
    response = client.get(endpoint, query_string={"limit": limit, "workflow": workflow})

    # THEN the response should be successful
    assert response.status_code == HTTPStatus.OK

    # THEN the response contains the correct number of orders
    assert len(response.json["orders"]) == expected_orders


def test_order_endpoint(
    client: FlaskClient,
    order: Order,
    order_another: Order,
):
    """Tests that the order endpoint returns the order with matching id"""
    # GIVEN a store with two orders

    order_id_to_fetch: int = order.id

    # WHEN a request is made to get a specific order
    endpoint: str = f"/api/v1/orders/{order_id_to_fetch}"
    response = client.get(endpoint)

    # THEN the response should be successful
    assert response.status_code == HTTPStatus.OK

    # THEN the response should only contain the specified order
    assert response.json == create_order_response(order).model_dump()


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
