from http import HTTPStatus

import mock.mock
import pytest
from flask.testing import FlaskClient

from cg.apps.tb import TrailblazerAPI
from cg.apps.tb.dto.summary_response import AnalysisSummary
from cg.constants.constants import Workflow
from cg.store.models import Order


@pytest.mark.parametrize(
    "limit, workflow, workflows, expected_orders",
    [
        (None, Workflow.MIP_DNA, [], 2),
        (1, Workflow.MIP_DNA, [], 1),
        (2, Workflow.MIP_DNA, [], 2),
        (None, Workflow.BALSAMIC, [], 1),
        (None, Workflow.FLUFFY, [], 0),
        (None, None, [], 3),
        (None, None, [Workflow.MIP_DNA], 2),
        (None, None, [Workflow.MIP_DNA, Workflow.BALSAMIC], 3),
        (None, None, [Workflow.BALSAMIC, Workflow.FLUFFY], 1),
        (1, None, [Workflow.MIP_DNA, Workflow.BALSAMIC], 1),
    ],
)
def test_orders_endpoint(
    client: FlaskClient,
    order: Order,
    order_another: Order,
    order_balsamic: Order,
    limit: int | None,
    workflow: str | None,
    workflows: list[str],
    expected_orders: int,
    analysis_summaries: list[AnalysisSummary],
):
    """Tests that orders are returned from the orders endpoint"""
    # GIVEN a store with three orders, two of which are MIP-DNA and the last is BALSAMIC

    # GIVEN the workflows selected for filtering the orders
    selected_workflows: list[str] = workflows or ([workflow] if workflow else [])
    expected_ids: set[int] = {
        order_entry.id
        for order_entry in (order, order_another, order_balsamic)
        if not selected_workflows or order_entry.workflow in selected_workflows
    }

    # WHEN a request is made to get all orders
    endpoint: str = "/api/v1/orders"
    with mock.patch.object(
        TrailblazerAPI,
        "get_summaries",
        return_value=analysis_summaries,
    ):
        response = client.get(
            endpoint,
            query_string={"pageSize": limit, "workflow": workflow, "workflows[]": workflows},
        )

    # THEN the response should be successful
    assert response.status_code == HTTPStatus.OK

    # THEN the response contains the correct orders
    assert len(response.json["orders"]) == expected_orders
    assert response.json["total_count"] == len(expected_ids)
    returned_ids = {item["id"] for item in response.json["orders"]}
    if limit and limit < len(expected_ids):
        assert returned_ids.issubset(expected_ids)
    else:
        assert returned_ids == expected_ids


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

    # THEN the response contains the specified order
    assert response.json["id"] == order_id_to_fetch


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


@pytest.mark.parametrize(
    "query_string, expected_error",
    [
        (
            {"workflow": Workflow.MIP_DNA, "workflows[]": [Workflow.BALSAMIC]},
            "Use either workflow or workflows[], not both",
        ),
        ({"workflows[]": ["invalid-workflow"]}, "Input should be"),
        ({"workflows[]": [Workflow.MIP_DNA, "invalid-workflow"]}, "Input should be"),
    ],
)
def test_orders_endpoint_invalid_workflow_filters(
    client: FlaskClient, query_string: dict, expected_error: str
):
    """Reject conflicting filters and invalid values in repeated workflow parameters."""
    response = client.get("/api/v1/orders", query_string=query_string)

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert expected_error in response.json["error"]
