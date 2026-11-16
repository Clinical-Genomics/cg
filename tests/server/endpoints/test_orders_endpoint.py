from http import HTTPStatus

import mock.mock
import pytest
from flask.testing import FlaskClient

from cg.apps.tb import TrailblazerAPI
from cg.apps.tb.dto.summary_response import AnalysisSummary
from cg.constants.constants import Workflow
from cg.store.models import Order


@pytest.mark.parametrize(
    "limit, workflow, workflows, expected_order_names, expected_total",
    [
        (None, Workflow.MIP_DNA, [], ["order", "order_another"], 2),
        (1, Workflow.MIP_DNA, [], ["order"], 2),
        (2, Workflow.MIP_DNA, [], ["order", "order_another"], 2),
        (None, Workflow.BALSAMIC, [], ["order_balsamic"], 1),
        (None, Workflow.FLUFFY, [], [], 0),
        (None, None, [], ["order", "order_another", "order_balsamic"], 3),
        (None, None, [Workflow.MIP_DNA], ["order", "order_another"], 2),
        (
            None,
            None,
            [Workflow.MIP_DNA, Workflow.BALSAMIC],
            ["order", "order_another", "order_balsamic"],
            3,
        ),
        (None, None, [Workflow.BALSAMIC, Workflow.FLUFFY], ["order_balsamic"], 1),
        (1, None, [Workflow.MIP_DNA, Workflow.BALSAMIC], ["order"], 3),
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
    expected_order_names: list[str],
    expected_total: int,
    analysis_summaries: list[AnalysisSummary],
):
    """Tests that orders are returned from the orders endpoint"""
    # GIVEN a store with three orders, two of which are MIP-DNA and the last is BALSAMIC

    orders_by_name = {
        "order": order,
        "order_another": order_another,
        "order_balsamic": order_balsamic,
    }
    expected_returned_ids = {orders_by_name[name].id for name in expected_order_names}

    # WHEN a request is made to get all orders
    endpoint: str = "/api/v1/orders"
    with mock.patch.object(
        TrailblazerAPI,
        "get_summaries",
        return_value=analysis_summaries,
    ):
        response = client.get(
            endpoint,
            query_string={
                "pageSize": limit,
                "workflow": workflow,
                "workflows[]": workflows,
                "sortField": "id",
                "sortOrder": "asc",
            },
        )

    # THEN the response should be successful
    assert response.status_code == HTTPStatus.OK

    # THEN the response contains the correct orders
    assert len(response.json["orders"]) == len(expected_order_names)
    assert response.json["total_count"] == expected_total
    returned_ids = {item["id"] for item in response.json["orders"]}
    assert returned_ids == expected_returned_ids


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
    "query_string",
    [
        {"workflow": Workflow.MIP_DNA, "workflows[]": [Workflow.BALSAMIC]},
        {"workflows[]": [Workflow.MIP_DNA, "invalid-workflow"]},
    ],
    ids=["conflicting-workflow-filters", "invalid-workflow"],
)
def test_orders_endpoint_invalid_workflow_filters(client: FlaskClient, query_string: dict):
    """Reject conflicting filters and invalid values in repeated workflow parameters."""
    response = client.get("/api/v1/orders", query_string=query_string)

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json["error"]
