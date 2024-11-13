from cg.constants import Workflow
from cg.services.orders.order_service.models import OrderQueryParams


def test_order_query_params_field_validator():
    """Test that the field validator expands the BALSAMIC workflow to include the UMI and QC workflows"""

    # GIVEN a order query params with BALSAMIC as workflow
    order_query_params = OrderQueryParams(workflows=[Workflow.BALSAMIC])

    # WHEN the field validator is called

    # THEN the BALSAMIC workflow should be expanded to include UMI and QC workflows
    assert order_query_params.workflows == [
        Workflow.BALSAMIC,
        Workflow.BALSAMIC_UMI,
        Workflow.BALSAMIC_QC,
    ]
