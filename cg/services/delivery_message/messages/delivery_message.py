from abc import ABC, abstractmethod

from cg.store.models import Case


class DeliveryMessage(ABC):
    @abstractmethod
    def generate_message(self, case: Case):
        pass
