from http import HTTPStatus

from flask.testing import FlaskClient

from cg.store.models import Case, Order


def test_get_delivery_message_single_case(client: FlaskClient, case: Case, order: Order):
    # GIVEN a case

    # WHEN a request is made to get a delivery message for the case
    response = client.get(f"/api/v1/cases/{case.internal_id}/delivery_message")

    # THEN the response should be successful
    assert response.status_code == HTTPStatus.OK

    # THEN the response contains a message
    assert response.json["message"]


def test_get_delivery_message_matching_order(
    client: FlaskClient, case: Case, case_in_same_order, order: Order
):
    # GIVEN a case

    # WHEN a request is made to get a delivery message for the case
    response = client.get(
        f"/api/v1/cases/delivery_message?case_ids={case.internal_id},{case_in_same_order.internal_id}"
    )

    # THEN the response should be successful
    assert response.status_code == HTTPStatus.OK

    # THEN the response contains a message
    assert response.json["message"]
