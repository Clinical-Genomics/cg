import logging

from cg.apps.environ import environ_email
from cg.meta.workflow.fastq import MipFastqHandler
from cg.services.analysis_starter.configurator.configurator import Configurator
from cg.services.analysis_starter.configurator.models.mip_dna import MIPDNACaseConfig
from cg.store.models import Case
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class MIPDNAConfigurator(Configurator):
    def __init__(self, fastq_handler: MipFastqHandler, store: Store):
        self.fastq_handler = fastq_handler
        self.store = store

    def configure(self, case_id: str, **flags) -> MIPDNACaseConfig:
        LOG.info(f"Configuring case {case_id}")
        self.fastq_handler.link_fastq_files(case_id)

    def get_config(self, case_id: str, **flags) -> MIPDNACaseConfig:
        case: Case = self.store.get_case_by_internal_id_strict(case_id)
        config = MIPDNACaseConfig(
            case_id=case_id,
            email=environ_email(),
            slurm_qos=case.slurm_priority,
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
