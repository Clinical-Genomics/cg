from http import HTTPStatus
from unittest import mock

import pytest
from flask.testing import FlaskClient

from cg.apps.tb import TrailblazerAPI
from cg.constants.tb import AnalysisStatus
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


@pytest.mark.parametrize(
    "analysis_status, expected_status_code",
    [
        (AnalysisStatus.COMPLETED, HTTPStatus.OK),
        (AnalysisStatus.RUNNING, HTTPStatus.PRECONDITION_FAILED),
    ],
)
def test_get_delivery_message_order(
    client: FlaskClient,
    server_case: Case,
    server_case_in_same_order: Case,
    order: Order,
    analysis_status: AnalysisStatus,
    expected_status_code: HTTPStatus,
):
    # GIVEN an order

    # WHEN a request is made to get a delivery message for the order
    with mock.patch.object(
        TrailblazerAPI, "get_latest_analysis_status", return_value=analysis_status
    ):
        response = client.get(f"/api/v1/orders/{order.id}/delivery_message")

        # THEN the response should have the expected status code
        assert response.status_code == expected_status_code
