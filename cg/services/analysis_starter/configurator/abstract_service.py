from abc import ABC

from cg.store.store import Store


class Configurator(ABC):

    def create_config(self, case_id: str):
        """Abstract method to create a case config for a case."""
        pass
