from abc import ABC, abstractmethod
from typing import TypeVar

from cg.services.analysis_starter.configurator.abstract_model import CaseConfig

SpecificCaseConfig = TypeVar("SpecificCaseConfig", bound=CaseConfig)


class Configurator(ABC):
    @abstractmethod
    def configure(self, case_id: str, **flags) -> CaseConfig:
        """Abstract method to configure a case."""
        pass

    @abstractmethod
    def get_config(self, case_id: str, **flags) -> CaseConfig:
        """Abstract method to get the (pre-existing) config for a case."""
        pass

    @staticmethod
    def _set_flags(config: SpecificCaseConfig, **flags) -> SpecificCaseConfig:
        curated_flags: dict = {key: value for key, value in flags.items() if value is not None}
        return config.model_copy(update=curated_flags)

    @abstractmethod
    def _ensure_required_config_files_exist(self, **kwargs) -> None:
        pass
