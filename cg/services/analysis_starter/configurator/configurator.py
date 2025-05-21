from abc import ABC, abstractmethod

from cg.services.analysis_starter.configurator.abstract_model import (
    CaseConfig,
    RunParameters,
    StartParameters,
)


class Configurator(ABC):

    @abstractmethod
    def configure(self, parameters: StartParameters) -> CaseConfig:
        """Abstract method to configure a case."""
        pass

    @abstractmethod
    def get_config(self, parameters: RunParameters) -> CaseConfig:
        """Abstract method to get the (pre-existing) config for a case."""
        pass
