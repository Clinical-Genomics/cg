from http import HTTPStatus

import pytest
from flask.testing import FlaskClient

from cg.store.models import Order


@pytest.mark.parametrize("limit", [None, 1])
def test_orders_endpoint(
    client: FlaskClient, order: Order, order_another: Order, limit: int | None
):
    """Tests that orders are returned from the orders endpoint"""
    # GIVEN a store with two orders

    # WHEN a request is made to get all orders
    endpoint: str = "/api/v1/orders"
    response = client.get(endpoint, query_string={"limit": limit})

    # THEN the response should be successful
    assert response.status_code == HTTPStatus.OK

    # THEN the response contains the correct number of orders
    if limit:
        assert len(response.json["orders"]) == 1
    else:
        assert len(response.json["orders"]) == 2
