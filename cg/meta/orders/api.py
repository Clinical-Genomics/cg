"""Unified interface to handle sample submissions.

This interface will update information in Status and/or LIMS as required.

The normal entry for information is through the REST API which will pass a JSON
document with all information about samples in the submission. The input will
be validated and if passing all checks be accepted as new samples.
"""

import logging

from cg.apps.lims import LimsAPI
from cg.meta.orders.ticket_handler import TicketHandler
from cg.models.orders.constants import OrderType
from cg.services.order_validation_service.models.order import Order
from cg.services.order_validation_service.order_validation_service import OrderValidationService
from cg.services.orders.store_order_services.store_order_service import StoreOrderService
from cg.services.orders.store_order_services.storing_service_registry import StoringServiceRegistry
from cg.store.models import User

LOG = logging.getLogger(__name__)


class OrdersAPI:
    """Orders API for accepting new samples into the system."""

    def __init__(
        self,
        lims: LimsAPI,
        ticket_handler: TicketHandler,
        storing_registry: StoringServiceRegistry,
        validation_service: OrderValidationService,
    ):
        super().__init__()
        self.lims = lims
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
