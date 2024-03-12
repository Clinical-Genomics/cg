from http import HTTPStatus
from unittest import mock

from flask.testing import FlaskClient

from cg.apps.tb import TrailblazerAPI
from cg.apps.tb.models import TrailblazerAnalysis
from cg.store.models import Case, Order


def test_get_delivery_message_single_case(client: FlaskClient, server_case: Case, order: Order):
    # GIVEN a case

    # WHEN a request is made to get a delivery message for the case
    response = client.get(f"/api/v1/cases/{server_case.internal_id}/delivery_message")

    # THEN the response should be successful
    assert response.status_code == HTTPStatus.OK

    # THEN the response contains a message
    assert response.json["message"]


def test_get_delivery_message_matching_order(
    client: FlaskClient, server_case: Case, server_case_in_same_order: Case, order: Order
):
    # GIVEN a case

    # WHEN a request is made to get a delivery message for the case
    response = client.get(
        f"/api/v1/cases/delivery_message?case_ids={server_case.internal_id},{server_case_in_same_order.internal_id}"
    )

    # THEN the response should be successful
    assert response.status_code == HTTPStatus.OK

    # THEN the response contains a message
    assert response.json["message"]


def test_get_delivery_message_order(
    client: FlaskClient,
    server_case: Case,
    trailblazer_analysis_for_server_case: TrailblazerAnalysis,
    server_case_in_same_order: Case,
    trailblazer_analysis_for_server_case_in_same_order: TrailblazerAnalysis,
    order: Order,
):
    """Tests that a delivery message is generated for an order with cases ready for delivery."""
    # GIVEN an order

    # WHEN a request is made to get a delivery message for the order

    # WHEN cases are ready to be delivered
    with mock.patch.object(
        TrailblazerAPI,
        "query_trailblazer",
        return_value={
            "analyses": [
                trailblazer_analysis_for_server_case.model_dump(),
                trailblazer_analysis_for_server_case_in_same_order.model_dump(),
            ]
        },
    ):
        response = client.get(f"/api/v1/orders/{order.id}/delivery_message")

        # THEN the response should be successful
        assert response.status_code == HTTPStatus.OK
        assert response.json["message"]


def test_get_delivery_message_order_missing_cases(
    client: FlaskClient,
    server_case: Case,
    trailblazer_analysis_for_server_case: TrailblazerAnalysis,
    server_case_in_same_order: Case,
    trailblazer_analysis_for_server_case_in_same_order: TrailblazerAnalysis,
    order: Order,
):
    """Tests that an error is returned for orders without any cases ready for delivery."""
    # GIVEN an order

    # WHEN a request is made to get a delivery message for the order

    # WHEN no cases are ready to be delivered
    with mock.patch.object(TrailblazerAPI, "query_trailblazer", return_value={"analyses": []}):
        response = client.get(f"/api/v1/orders/{order.id}/delivery_message")

        # THEN the response should not be successful
        assert response.status_code == HTTPStatus.PRECONDITION_FAILED
        assert response.json["error"]
