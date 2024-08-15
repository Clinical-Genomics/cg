"""Module for a generic order submitter."""

from cg.models.orders.order import OrderIn
from cg.services.orders.store_order_services.store_generic_order import StoreGenericOrderService
from cg.services.orders.submitters.order_submitter import OrderSubmitter
from cg.services.orders.validate_order_services.validate_generic_order import (
    ValidateGenericOrderService,
)


class GenericOrderSubmitter(OrderSubmitter):
    """
    Class for submitting generic orders.
    This class is used to submit orders for the following workflows:
    - Balsamic
    - Balsamic QC
    - Balsamic UMI
    - MIP DNA
    - MIP RNA
    - Tomte
    """

    def __init__(
        self,
        order_validation_service: ValidateGenericOrderService,
        order_store_service: StoreGenericOrderService,
    ):
        self.order_validation_service = order_validation_service
        self.order_store_service = order_store_service

    def submit_order(self, order_in: OrderIn) -> dict:
        """Submit a generic order."""
        self.order_validation_service.validate_order(order_in)
        result: dict = self.order_store_service.store_order(order_in)
        return result
