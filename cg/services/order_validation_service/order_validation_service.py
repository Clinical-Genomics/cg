from abc import ABC, abstractmethod

from cg.services.order_validation_service.models.errors import ValidationErrors


class OrderValidationService(ABC):
    @abstractmethod
    def _get_errors(self, order_json: str) -> dict:
        pass
