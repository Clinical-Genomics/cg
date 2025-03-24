import logging
from abc import abstractmethod

from cg.services.analysis_starter.configurator.abstract_model import CaseConfig

LOG = logging.getLogger(__name__)


class Configurator:

    @abstractmethod
    def configure(self, case_id: str) -> CaseConfig:
        """Abstract method to configure a case."""
        pass

    @abstractmethod
    def get_config(self, case_id: str) -> CaseConfig:
        """Abstract method to get the (pre-existing) config for a case."""
        pass
