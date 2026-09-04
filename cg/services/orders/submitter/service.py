"""Unified interface to handle sample submissions.

This service will update information in Status and/or LIMS as required.

The normal entry for information is through the REST API which will pass a JSON
document with all information about samples in the submission. The input will
be validated and if passing all checks be accepted as new samples.
"""

import logging

from cg.models.cg_config import NatsConfig
from cg.models.orders.constants import OrderType
from cg.services.events import event_publisher
from cg.services.orders.storing.service import StoreOrderService
from cg.services.orders.storing.service_registry import StoringServiceRegistry
from cg.services.orders.submitter.ticket_handler import TicketHandler
from cg.services.orders.validation.models.order import Order
from cg.services.orders.validation.service import OrderValidationService
from cg.store.models import User
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class OrderSubmitter:
    """Orders API for accepting new samples into the system."""

    def __init__(
        self,
        status_db: Store,
        storing_registry: StoringServiceRegistry,
        ticket_handler: TicketHandler,
        validation_service: OrderValidationService,
        nats_config: NatsConfig,
    ):
        super().__init__()
        self.status_db = status_db
        self.storing_registry = storing_registry
        self.ticket_handler = ticket_handler
        self.validation_service = validation_service
        self.nats_config = nats_config

    def submit(self, order_type: OrderType, raw_order: dict, user: User) -> dict:
        """Submit a batch of samples. Publishes event if there are external samples.

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
        serialized_order: dict = storing_service.store_order(order)
        if external_samples := order.external_samples(self.status_db):
            sample_names: list[str] = [sample.name for sample in external_samples]
            LOG.info(f"Order contains external samples {sample_names}")
            customer_internal_id: str = order.customer
            payload: dict = _get_payload_for_external_samples(
                customer_internal_id=customer_internal_id, sample_names=sample_names
            )
            subject = "external.samples_ordered"
            LOG.info(f"Publishing event to subject {subject} with payload {payload}")
            event_publisher.publish(
                nats_config=self.nats_config,
                subject=subject,
                event_payload=payload,
            )
        return serialized_order


def _get_payload_for_external_samples(customer_internal_id: str, sample_names: list[str]) -> dict:
    return {"status_db.customer": customer_internal_id, "status_db.sample_names": sample_names}
