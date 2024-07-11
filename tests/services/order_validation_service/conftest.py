import pytest
from cg.constants.constants import DataDelivery, Workflow
from cg.services.order_validation_service.models.order import Order


@pytest.fixture
def valid_order() -> Order:
    return Order(
        connect_to_ticket=True,
        delivery_type=DataDelivery.ANALYSIS_FILES,
        name="name",
        ticket_number="#12345",
        workflow=Workflow.BALSAMIC,
        customer="customer",
    )
