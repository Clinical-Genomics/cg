"""Abstract base classes for order submitters."""

import logging
from abc import ABC, abstractmethod

from cg.services.orders.lims_service.service import OrderLimsService
from cg.services.orders.validation.models.order import Order
from cg.services.orders.validation.models.sample import Sample
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class StoreOrderService(ABC):
    @abstractmethod
    def __init__(self, status_db: Store, lims_service: OrderLimsService):
        self.status_db = status_db
        self.lims = lims_service

    @abstractmethod
    def store_order(self, order: Order):
        pass

    @staticmethod
    def _fill_in_sample_ids(samples: list[Sample], lims_map: dict) -> None:
        """Fill in LIMS sample ids."""
        for sample in samples:
            LOG.debug(f"{sample.name}: link sample to LIMS")
            internal_id = lims_map[sample.name]
            LOG.info(f"{sample.name} -> {internal_id}: connect sample to LIMS")
            sample._generated_lims_id = internal_id
