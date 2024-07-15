from abc import ABC, abstractmethod

from cg.services.order_validation_service.models.errors import ValidationError


class OrderValidationService(ABC):
    @abstractmethod
    def validate(self, order_json: str) -> list[ValidationError]:
        pass
