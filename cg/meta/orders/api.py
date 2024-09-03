"""Unified interface to handle sample submissions.

This interface will update information in Status and/or LIMS as required.

The normal entry for information is through the REST API which will pass a JSON
document with all information about samples in the submission. The input will
be validated and if passing all checks be accepted as new samples.
"""

import logging

from cg.apps.lims import LimsAPI
from cg.meta.orders.ticket_handler import TicketHandler
from cg.models.orders.order import OrderIn, OrderType
from cg.services.orders.submitters.order_submitter_registry import (
    OrderSubmitterRegistry,
)
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class OrdersAPI:
    """Orders API for accepting new samples into the system."""

    def __init__(
        self,
        lims: LimsAPI,
        status: Store,
        ticket_handler: TicketHandler,
        submitter_registry: OrderSubmitterRegistry,
    ):
        super().__init__()
        self.lims = lims
        self.status = status
        self.ticket_handler = ticket_handler
        self.submitter_registry = submitter_registry

    def submit(self, project: OrderType, order_in: OrderIn, user_name: str, user_mail: str) -> dict:
        """Submit a batch of samples.

        Main entry point for the class towards interfaces that implements it.
        """
        submit_handler = self.submitter_registry.get_order_submitter(project)
        submit_handler.order_validation_service.validate_order(order_in)
        # detect manual ticket assignment
        ticket_number: str | None = self.ticket_handler.parse_ticket_number(order_in.name)
        if not ticket_number:
            ticket_number = self.ticket_handler.create_ticket(
                order=order_in, user_name=user_name, user_mail=user_mail, project=project
            )
        else:
            self.ticket_handler.connect_to_ticket(
                order=order_in,
                user_name=user_name,
                project=project,
                ticket_number=ticket_number,
            )
        order_in.ticket = ticket_number
        return submit_handler.submit_order(order_in=order_in)
