import pytest

from cg.constants import Workflow
from cg.services.orders.order_service.models import OrderQueryParams


@pytest.mark.parametrize(
    "workflow, expected_workflows",
    [
        ([Workflow.BALSAMIC], [Workflow.BALSAMIC, Workflow.BALSAMIC_UMI]),
        ([Workflow.MIP_DNA], [Workflow.MIP_DNA]),
        (
            [Workflow.BALSAMIC, Workflow.RNAFUSION],
            [Workflow.BALSAMIC, Workflow.RNAFUSION, Workflow.BALSAMIC_UMI],
        ),
        (
            [Workflow.BALSAMIC, Workflow.BALSAMIC_UMI],
            [Workflow.BALSAMIC, Workflow.BALSAMIC_UMI],
        ),
        ([], []),
    ],
    ids=[
        "balsamic-adds-umi",
        "other-workflows-unchanged",
        "balsamic-preserves-rnafusion",
        "umi-not-duplicated",
        "empty-workflows",
    ],
)
def test_order_query_params_field_validator(
    workflow: list[Workflow], expected_workflows: list[Workflow]
):
    """Test Balsamic expansion preserves other workflows without duplicating UMI."""

    # GIVEN workflow selections and their expected expansion

    # WHEN creating query parameters, which runs the validator
    order_query_params = OrderQueryParams(workflows=workflow)

    # THEN the workflows match the expected result
    assert order_query_params.workflows == expected_workflows
