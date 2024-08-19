from abc import ABC, abstractmethod


class OrderValidationService(ABC):
    @abstractmethod
    def validate(self, raw_order: dict) -> dict:
        pass
