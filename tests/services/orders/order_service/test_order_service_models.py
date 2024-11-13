import pytest

from cg.constants import Workflow
from cg.services.orders.order_service.models import OrderQueryParams


@pytest.mark.parametrize(
    "workflow, expected_workflows",
    [
        ([Workflow.BALSAMIC], [Workflow.BALSAMIC, Workflow.BALSAMIC_UMI, Workflow.BALSAMIC_QC]),
        ([Workflow.MIP_DNA], [Workflow.MIP_DNA]),
    ],
)
def test_order_query_params_field_validator(workflow: Workflow, expected_workflows: list[Workflow]):
    """Test that the field validator expands the BALSAMIC workflow to include the UMI and QC workflows"""

    # GIVEN a order query params with BALSAMIC as workflow
    order_query_params = OrderQueryParams(workflows=workflow)

    # WHEN the field validator is called

    # THEN the BALSAMIC workflow should be expanded to include UMI and QC workflows
    assert order_query_params.workflows == expected_workflows
