from abc import ABC

from cg.models.cg_config import CGConfig
from cg.store.store import Store


class Configurator(ABC):

    def __init__(self, cg_config: CGConfig):
        self.store: Store = cg_config.status_db

    def create_config(self, case_id: str):
        """Abstract method to create a case config for a case."""
        pass
