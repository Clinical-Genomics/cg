from cg.services.analysis_starter.configurator.configurator import Configurator
from cg.services.analysis_starter.configurator.models.mip_dna import MIPDNACaseConfig


class MIPDNAConfigurator(Configurator):

    def configure(self, case_id: str, **flags) -> MIPDNACaseConfig:
        pass

    def get_config(self, case_id: str, **flags) -> MIPDNACaseConfig:
        pass

    @staticmethod
    def _ensure_valid_config(config: MIPDNACaseConfig) -> None:
        pass
