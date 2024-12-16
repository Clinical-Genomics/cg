"""Unified interface to handle sample submissions.

This interface will update information in Status and/or LIMS as required.

The normal entry for information is through the REST API which will pass a JSON
document with all information about samples in the submission. The input will
be validated and if passing all checks be accepted as new samples.
"""

import logging

from cg.apps.lims import LimsAPI
from cg.meta.orders.ticket_handler import TicketHandler
from cg.models.orders.order import OrderType
from cg.services.order_validation_service.models.order import Order
from cg.services.order_validation_service.order_type_maps import (
    ORDER_TYPE_MODEL_MAP,
    ORDER_TYPE_RULE_SET_MAP,
)
from cg.services.orders.submitters.order_submitter import OrderSubmitter
from cg.services.orders.submitters.order_submitter_registry import OrderSubmitterRegistry
from cg.store.models import User
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

    def submit(self, order_type: OrderType, raw_order: dict, user: User) -> dict:
        """Submit a batch of samples.

        Main entry point for the class towards interfaces that implements it.
        """
        submit_handler: OrderSubmitter = self.submitter_registry.get_order_submitter(order_type)
        order_model = ORDER_TYPE_MODEL_MAP[order_type]
        rule_set = ORDER_TYPE_RULE_SET_MAP[order_type]
        order: Order = submit_handler.order_validation_service.parse_and_validate(
            raw_order=raw_order, model=order_model, rule_set=rule_set
        )
        ticket_number: int = self.ticket_handler.create_ticket(
            order=order, user_name=user.name, user_mail=user.email, order_type=order_type
        )
        order.ticket_number = ticket_number
        return submit_handler.submit_order(order)
