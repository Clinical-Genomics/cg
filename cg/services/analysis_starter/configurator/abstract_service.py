from abc import ABC


class Configurator(ABC):

    def create_config(self, case_id: str, dry_run: bool = False):
        """Abstract method to create a case config for a case."""
        pass
