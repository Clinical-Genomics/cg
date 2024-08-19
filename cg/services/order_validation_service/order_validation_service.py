from abc import ABC, abstractmethod


class OrderValidationService(ABC):
    @abstractmethod
    def validate(self, order_json: str) -> dict:
        pass
