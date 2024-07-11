from cg.constants.constants import DataDelivery, Workflow
from cg.services.order_validation_service.models.order import Order
from cg.services.order_validation_service.validators.inter_field_validators import (
    validate_ticket_number_required_if_connected,
)


def test_ticket_is_required():
    # GIVEN an order that should be connected to a ticket but is missing a ticket number
    order = Order(
        connect_to_ticket=True,
        delivery_type=DataDelivery.ANALYSIS_FILES,
        name="name",
        ticket_number=None,
        workflow=Workflow.BALSAMIC,
        customer="customer",
    )

    # WHEN validating the order
    errors = validate_ticket_number_required_if_connected(order)

    # THEN an error should be returned
    assert errors
