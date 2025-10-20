import logging
from pathlib import Path

from cg.apps.environ import environ_email
from cg.exc import MissingConfigFilesError
from cg.meta.workflow.fastq import MipFastqHandler
from cg.models.cg_config import MipConfig
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
        cg_mip_config: MipConfig,
        config_file_creator: MIPDNAConfigFileCreator,
        fastq_handler: MipFastqHandler,
        gene_panel_file_creator: GenePanelFileCreator,
        managed_variants_file_creator: ManagedVariantsFileCreator,
        store: Store,
    ):
        self.conda_binary = cg_mip_config.conda_binary
        self.conda_environment = cg_mip_config.conda_env
        self.pipeline_binary = cg_mip_config.script
        self.pipeline_command = cg_mip_config.workflow
        self.pipeline_config_path = cg_mip_config.mip_config
        self.root = cg_mip_config.root

        self.config_file_creator = config_file_creator
        self.fastq_handler = fastq_handler
        self.gene_panel_file_creator = gene_panel_file_creator
        self.managed_variants_file_creator = managed_variants_file_creator
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
        config: MIPDNACaseConfig = self.get_config(case_id=case_id, **flags)
        LOG.info(f"Case {case_id} configured successfully")
        return config

    def get_config(self, case_id: str, **flags) -> MIPDNACaseConfig:
        case: Case = self.store.get_case_by_internal_id_strict(case_id)
        config = MIPDNACaseConfig(
            case_id=case_id,
            conda_binary=self.conda_binary,
            conda_environment=self.conda_environment,
            pipeline_binary=self.pipeline_binary,
            pipeline_command=self.pipeline_command,
            pipeline_config_path=self.pipeline_config_path,
            email=environ_email(),
            slurm_qos=case.slurm_priority,
            use_bwa_mem=flags.get("use_bwa_mem", False),
        )
        config = self._set_flags(config=config, **flags)
        self._ensure_required_config_files_exist(case_id)
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

    def _ensure_required_config_files_exist(self, case_id: str) -> None:
        """Ensures that the case run directory has a MIP config file, a gene panel file and a
        managed variants file.
        Raises:
            MissingConfigFilesError if any of those files are not present.
        """
        config_file_path: Path = self._get_config_file_path(case_id)
        gene_panel_file_path: Path = self._get_gene_panel_file_path(case_id)
        managed_variants_file_path: Path = self._get_managed_variants_file_path(case_id)
        if not (
            config_file_path.exists()
            and gene_panel_file_path.exists()
            and managed_variants_file_path.exists()
        ):
            raise MissingConfigFilesError(
                "Ensure config file, gene panel and managed variants files exist."
            )
