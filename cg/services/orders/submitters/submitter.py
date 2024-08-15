"""Abstract base classes for order submitters."""

from abc import ABC, abstractmethod

from cg.models.orders.order import OrderIn
from cg.services.orders.order_lims_service.order_lims_service import OrderLimsService
from cg.store.store import Store


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


class Submitter(ABC):
    @abstractmethod
    def __init__(
        self,
        validate_order_service: ValidateOrderService,
        store_order_service: StoreOrderService,
    ):
        self.order_validation_service = validate_order_service
        self.order_store_service = store_order_service

    @abstractmethod
    def submit_order(self, order_in: OrderIn) -> dict:
        pass
