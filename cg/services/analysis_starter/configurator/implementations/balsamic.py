import logging
from pathlib import Path

from cg.apps.lims import LimsAPI
from cg.exc import CaseNotConfiguredError
from cg.meta.workflow.fastq import BalsamicFastqHandler
from cg.models.cg_config import BalsamicConfig
from cg.services.analysis_starter.configurator.configurator import Configurator
from cg.services.analysis_starter.configurator.file_creators.balsamic_config import (
    BalsamicConfigFileCreator,
)
from cg.services.analysis_starter.configurator.models.balsamic import BalsamicCaseConfig
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class BalsamicConfigurator(Configurator):
    def __init__(
        self,
        config: BalsamicConfig,
        config_file_creator: BalsamicConfigFileCreator,
        fastq_handler: BalsamicFastqHandler,
        lims_api: LimsAPI,
        store: Store,
    ):
        self.store: Store = store
        self.lims_api: LimsAPI = lims_api
        self.conda_binary: Path = config.conda_binary
        self.balsamic_binary: Path = config.binary_path
        self.root_dir: Path = config.root
        self.fastq_handler: BalsamicFastqHandler = fastq_handler
        self.bed_directory: Path = config.bed_path
        self.cache_dir: Path = config.balsamic_cache
        self.cadd_path: Path = config.cadd_path
        self.default_cluster_config: Path = config.cluster_config
        self.genome_interval_path: Path = config.genome_interval_path
        self.gens_coverage_female_path: Path = config.gens_coverage_female_path
        self.gens_coverage_male_path: Path = config.gens_coverage_male_path
        self.gnomad_af5_path: Path = config.gnomad_af5_path
        self.environment: str = config.conda_env
        self.sentieon_licence_path: Path = config.sentieon_licence_path
        self.sentieon_licence_server: str = config.sentieon_licence_server
        self.loqusdb_artefact_snv: Path = config.loqusdb_artefact_snv
        self.loqusdb_artefact_sv: Path = config.loqusdb_artefact_sv
        self.loqusdb_cancer_germline_snv: Path = config.loqusdb_cancer_germline_snv
        self.loqusdb_cancer_somatic_snv: Path = config.loqusdb_cancer_somatic_snv
        self.loqusdb_cancer_somatic_sv: Path = config.loqusdb_cancer_somatic_sv
        self.loqusdb_clinical_snv: Path = config.loqusdb_clinical_snv
        self.loqusdb_clinical_sv: Path = config.loqusdb_clinical_sv
        self.pon_directory: Path = config.pon_path
        self.slurm_account: str = config.slurm.account
        self.slurm_mail_user: str = config.slurm.mail_user
        self.swegen_snv: Path = config.swegen_snv
        self.swegen_sv: Path = config.swegen_sv
        self.config_file_creator: BalsamicConfigFileCreator = config_file_creator

    def configure(self, case_id: str, **flags) -> BalsamicCaseConfig:
        LOG.info(f"Configuring case {case_id}")
        self.fastq_handler.link_fastq_files(case_id)
        self.config_file_creator.create(case_id=case_id, **flags)
        return self.get_config(case_id=case_id, **flags)

    def get_config(self, case_id: str, **flags) -> BalsamicCaseConfig:
        balsamic_config: BalsamicCaseConfig = BalsamicCaseConfig(
            account=self.slurm_account,
            binary=self.balsamic_binary,
            case_id=case_id,
            conda_binary=self.conda_binary,
            cluster_config=self.default_cluster_config,
            environment=self.environment,
            mail_user=self.slurm_mail_user,
            qos=self.store.get_case_by_internal_id_strict(case_id).slurm_priority,
            sample_config=self._get_sample_config_path(case_id),
        )
        balsamic_config: BalsamicCaseConfig = self._set_flags(config=balsamic_config, **flags)
        self._ensure_required_config_files_exist(balsamic_config)
        return balsamic_config

    def _get_sample_config_path(self, case_id: str) -> Path:
        return Path(self.root_dir, case_id, f"{case_id}.json")

    def _ensure_required_config_files_exist(self, config: BalsamicCaseConfig) -> None:
        if not config.sample_config.exists():
            raise CaseNotConfiguredError(
                f"Please ensure that the config file {config.sample_config.exists()} exists."
            )
