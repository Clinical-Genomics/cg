import logging
from pathlib import Path

from cg.apps.environ import environ_email
from cg.exc import CaseNotConfiguredError
from cg.meta.workflow.fastq import MipFastqHandler
from cg.services.analysis_starter.configurator.configurator import Configurator
from cg.services.analysis_starter.configurator.file_creators.gene_panel import GenePanelFileCreator
from cg.services.analysis_starter.configurator.file_creators.managed_variants import (
    ManagedVariantsFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.mip_dna_config import (
    MIPDNAConfigFileCreator,
)
from cg.services.analysis_starter.configurator.models.mip_dna import MIPDNACaseConfig
from cg.store.models import Case
from cg.store.store import Store

LOG = logging.getLogger(__name__)

MIP_DNA_CONFIG_FILE_NAME = "pedigree.yaml"
MIP_DNA_GENE_PANEL_FILE_NAME = "gene_panels.bed"
MIP_DNA_MANAGED_VARIANTS_FILE_NAME = "managed_variants.vcf"


class MIPDNAConfigurator(Configurator):
    def __init__(
        self,
        config_file_creator: MIPDNAConfigFileCreator,
        fastq_handler: MipFastqHandler,
        gene_panel_file_creator: GenePanelFileCreator,
        managed_variants_file_creator: ManagedVariantsFileCreator,
        root: Path,
        store: Store,
    ):
        self.config_file_creator = config_file_creator
        self.fastq_handler = fastq_handler
        self.gene_panel_file_creator = gene_panel_file_creator
        self.managed_variants_file_creator = managed_variants_file_creator
        self.root = root
        self.store = store

    def configure(self, case_id: str, **flags) -> MIPDNACaseConfig:
        LOG.info(f"Configuring case {case_id}")
        self._create_run_directory(case_id)
        self.fastq_handler.link_fastq_files(case_id)
        self.config_file_creator.create(
            case_id=case_id,
            bed_flag=flags.get("panel_bed"),
            file_path=self._get_config_file_path(case_id=case_id),
        )
        self.gene_panel_file_creator.create(
            case_id=case_id, file_path=self._get_gene_panel_file_path(case_id)
        )
        self.managed_variants_file_creator.create(
            case_id=case_id, file_path=self._get_managed_variants_file_path(case_id)
        )
        return self.get_config(case_id=case_id, **flags)

    def get_config(self, case_id: str, **flags) -> MIPDNACaseConfig:
        case: Case = self.store.get_case_by_internal_id_strict(case_id)
        config = MIPDNACaseConfig(
            case_id=case_id,
            email=environ_email(),
            slurm_qos=case.slurm_priority,
        )
        config = self._set_flags(config=config, **flags)
        self._ensure_valid_config(case_id)
        return config

    def _get_gene_panel_file_path(self, case_id: str) -> Path:
        return Path(self._get_run_directory(case_id), MIP_DNA_GENE_PANEL_FILE_NAME)

    def _get_managed_variants_file_path(self, case_id: str) -> Path:
        return Path(self._get_run_directory(case_id), MIP_DNA_MANAGED_VARIANTS_FILE_NAME)

    def _get_config_file_path(self, case_id: str) -> Path:
        return Path(self._get_run_directory(case_id), MIP_DNA_CONFIG_FILE_NAME)

    def _get_run_directory(self, case_id: str) -> Path:
        return Path(self.root, case_id)

    def _create_run_directory(self, case_id: str) -> Path:
        path: Path = self._get_run_directory(case_id)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _ensure_valid_config(self, case_id: str) -> None:
        """Ensures that the case run directory has a MIP config file, a gene panel file and a
        managed variants file.
        Raises:
            CaseNotConfiguredError if any of those files are not present.
        """
        config_file_path: Path = self._get_config_file_path(case_id)
        gene_panel_file_path: Path = self._get_gene_panel_file_path(case_id)
        managed_variants_file_path: Path = self._get_managed_variants_file_path(case_id)
        if not (
            config_file_path.exists()
            and gene_panel_file_path.exists()
            and managed_variants_file_path.exists()
        ):
            raise CaseNotConfiguredError(
                "Ensure config file, gene panel and managed variants files exist."
            )

    @staticmethod
    def _set_flags(config: MIPDNACaseConfig, **flags) -> MIPDNACaseConfig:
        if flags.get("use_bwa_mem"):
            flags["bwa_mem"] = 1
            flags["bwa_mem2"] = 0
            flags.pop("use_bwa_mem")
        return Configurator._set_flags(config=config, **flags)
