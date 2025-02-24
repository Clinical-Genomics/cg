from abc import ABC

from cg.store.store import Store


class Configurator(ABC):

    def __init__(self, store: Store):
        self.store: Store = store

    def create_config(self, case_id: str):
        """Abstract method to create a case config for a case."""
        pass
