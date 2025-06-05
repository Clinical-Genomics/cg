from abc import ABC, abstractmethod

from cg.services.analysis_starter.configurator.abstract_model import CaseConfig


class Configurator(ABC):

    @abstractmethod
    def configure(self, case_id: str, **flags) -> CaseConfig:
        """Abstract method to configure a case."""
        pass

    @abstractmethod
    def get_config(self, case_id: str, **flags) -> CaseConfig:
        """Abstract method to get the (pre-existing) config for a case."""
        pass
