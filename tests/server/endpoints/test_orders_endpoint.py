from http import HTTPStatus

from flask.testing import FlaskClient

from cg.store.models import Order


def test_orders_endpoint(client: FlaskClient, order: Order):
    """Tests that orders are returned from the orders endpoint"""
    # GIVEN an order

    # WHEN a request is made to get all orders
    response = client.get("/api/v1/orders")

    # THEN the response should be successful
    assert response.status_code == HTTPStatus.OK

    # THEN the response contains an order
    assert len(response.json["orders"]) == 1
