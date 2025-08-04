from cg.services.analysis_starter.configurator.configurator import Configurator
from cg.services.analysis_starter.configurator.models.mip_dna import MIPDNACaseConfig


class MIPDNAConfigurator(Configurator):

    def configure(self, case_id: str, **flags) -> MIPDNACaseConfig:
        pass

    def get_config(self, case_id: str, **flags) -> MIPDNACaseConfig:

        config = MIPDNACaseConfig(case_id=case_id)
        return self._set_flags(config=config, **flags)

    @staticmethod
    def _ensure_valid_config(config: MIPDNACaseConfig) -> None:
        pass

    @staticmethod
    def _set_flags(config: MIPDNACaseConfig, **flags) -> MIPDNACaseConfig:
        if flags.get("use_bwa_mem"):
            flags["bwa_mem"] = 1
            flags["bwa_mem2"] = 0
            flags.pop("use_bwa_mem")
        return Configurator._set_flags(config=config, **flags)
