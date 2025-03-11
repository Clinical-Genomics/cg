from abc import ABC

from cg.services.analysis_starter.configurator.abstract_model import CaseConfig


class Configurator(ABC):

    def create_config(self, case_id: str) -> CaseConfig:
        """Abstract method to create a case config for a case."""
        pass
