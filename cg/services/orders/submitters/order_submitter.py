"""Abstract base classes for order submitters."""

import logging
from abc import ABC, abstractmethod

from cg.models.orders.order import OrderIn
from cg.services.order_validation_service.models.sample import Sample
from cg.services.order_validation_service.order_validation_service import OrderValidationService
from cg.services.orders.order_lims_service.order_lims_service import OrderLimsService
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class ValidateOrderService(ABC):
    @abstractmethod
    def __init__(self, status_db: Store):
        self.status_db = status_db

    @abstractmethod
    def validate_order(self, order_in: OrderIn):
        pass


class StoreOrderService(ABC):
    @abstractmethod
    def __init__(self, status_db: Store, lims_service: OrderLimsService):
        self.status_db = status_db
        self.lims = lims_service

    @abstractmethod
    def store_order(self, order_in: OrderIn):
        pass

    @staticmethod
    def _fill_in_sample_ids(samples: list[Sample], lims_map: dict):
        """Fill in LIMS sample ids."""
        for sample in samples:
            LOG.debug(f"{sample.name}: link sample to LIMS")
            internal_id = lims_map[sample.name]
            LOG.info(f"{sample.name} -> {internal_id}: connect sample to LIMS")
            sample._generated_lims_id = internal_id


class OrderSubmitter(ABC):
    @abstractmethod
    def __init__(
        self,
        validate_order_service: OrderValidationService,
        store_order_service: StoreOrderService,
    ):
        self.order_validation_service = validate_order_service
        self.order_store_service = store_order_service

    @abstractmethod
    def submit_order(self, order_in: OrderIn) -> dict:
        pass
