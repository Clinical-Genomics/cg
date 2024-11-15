from abc import ABC, abstractmethod

from cg.services.order_validation_service.models.order import Order


class OrderValidationService(ABC):
    @abstractmethod
    def validate(self, raw_order: dict) -> dict:
        pass

    @abstractmethod
    def parse_and_validate(self, raw_order: dict) -> Order:
        pass
