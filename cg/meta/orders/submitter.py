import datetime as dt
import logging
from abc import ABC, abstractmethod

from cg.apps.lims import LimsAPI
from cg.models.orders.order import OrderIn
from cg.store.models import Base
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class Submitter(ABC):
    def __init__(self, lims: LimsAPI, status: Store):
        self.lims = lims
        self.status = status

    def validate_order(self, order: OrderIn) -> None:
        """Part of Submitter interface, base implementation"""

    @abstractmethod
    def submit_order(self, order: OrderIn) -> dict:
        pass

    @staticmethod
    @abstractmethod
    def order_to_status(order: OrderIn) -> dict:
        pass

    @abstractmethod
    def store_items_in_status(
        self, customer_id: str, order: str, ordered: dt.datetime, ticket_id: int, items: list[dict]
    ) -> list[Base]:
        pass

    @staticmethod
    def _fill_in_sample_ids(samples: list[dict], lims_map: dict, id_key: str = "internal_id"):
        """Fill in LIMS sample ids."""
        for sample in samples:
            LOG.debug(f"{sample['name']}: link sample to LIMS")
            if not sample.get(id_key):
                internal_id = lims_map[sample["name"]]
                LOG.info(f"{sample['name']} -> {internal_id}: connect sample to LIMS")
                sample[id_key] = internal_id
