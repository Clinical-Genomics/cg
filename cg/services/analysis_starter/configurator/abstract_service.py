from abc import ABC

from cg.services.analysis_starter.configurator.abstract_model import CaseConfig


class Configurator(ABC):

    def configure(self, case_id: str) -> CaseConfig:
        """Abstract method to configure a case."""
        pass

    def get_config(self, case_id: str) -> CaseConfig:
        """Abstract method to get the (pre-existing) config for a case."""
        pass
