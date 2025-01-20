"""Unified interface to handle sample submissions.

This service will update information in Status and/or LIMS as required.

The normal entry for information is through the REST API which will pass a JSON
document with all information about samples in the submission. The input will
be validated and if passing all checks be accepted as new samples.
"""

from cg.models.orders.constants import OrderType
from cg.services.orders.storing.service import StoreOrderService
from cg.services.orders.storing.service_registry import StoringServiceRegistry
from cg.services.orders.submitter.ticket_handler import TicketHandler
from cg.services.orders.validation.models.order import Order
from cg.services.orders.validation.service import OrderValidationService
from cg.store.models import User


class OrderSubmitter:
    """Orders API for accepting new samples into the system."""

    def __init__(
        self,
        ticket_handler: TicketHandler,
        storing_registry: StoringServiceRegistry,
        validation_service: OrderValidationService,
    ):
        super().__init__()
        self.ticket_handler = ticket_handler
        self.storing_registry = storing_registry
        self.validation_service = validation_service

    def submit(self, order_type: OrderType, raw_order: dict, user: User) -> dict:
        """Submit a batch of samples.

        Main entry point for the class towards interfaces that implements it.
        """
        storing_service: StoreOrderService = self.storing_registry.get_storing_service(order_type)
        order: Order = self.validation_service.parse_and_validate(
            raw_order=raw_order, order_type=order_type, user_id=user.id
        )
        ticket_number: int = self.ticket_handler.create_ticket(
            order=order, user_name=user.name, user_mail=user.email, order_type=order_type
        )
        order._generated_ticket_id = ticket_number
        return storing_service.store_order(order)
