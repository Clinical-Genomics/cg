from abc import ABC, abstractmethod

from cg.services.order_validation_service.models.errors import ValidationErrors


class OrderValidationService(ABC):
    @abstractmethod
    def validate(self, order_json: str) -> ValidationErrors:
        pass
