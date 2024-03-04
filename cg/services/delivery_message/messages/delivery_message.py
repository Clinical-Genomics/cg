from abc import ABC, abstractmethod

from cg.store.models import Case


class DeliveryMessage(ABC):
    @abstractmethod
    def create_message(self, case: Case) -> str:
        pass
