from cg.apps.environ import environ_email
from cg.services.analysis_starter.configurator.configurator import Configurator
from cg.services.analysis_starter.configurator.models.mip_dna import MIPDNACaseConfig
from cg.store.store import Store


class MIPDNAConfigurator(Configurator):
    def __init__(self, store: Store):
        self.store = store

    def configure(self, case_id: str, **flags) -> MIPDNACaseConfig:
        pass

    def get_config(self, case_id: str, **flags) -> MIPDNACaseConfig:
        case = self.store.get_case_by_internal_id(case_id)
        config = MIPDNACaseConfig(
            case_id=case_id, email=environ_email(), slurm_qos=case.slurm_priority
        )
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
