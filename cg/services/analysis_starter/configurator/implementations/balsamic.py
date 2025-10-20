import logging
import re
from pathlib import Path

from cg.apps.lims import LimsAPI
from cg.constants import SexOptions
from cg.exc import BalsamicMissingTumorError, BedFileNotFoundError, CaseNotConfiguredError
from cg.meta.workflow.fastq import BalsamicFastqHandler
from cg.models.cg_config import BalsamicConfig
from cg.services.analysis_starter.configurator.configurator import Configurator
from cg.services.analysis_starter.configurator.file_creators.balsamic_config import (
    BalsamicConfigFileCreator,
)
from cg.services.analysis_starter.configurator.models.balsamic import BalsamicCaseConfig
from cg.store.models import Case, Sample
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

    @staticmethod
    def _get_patient_sex(case) -> SexOptions:
        sample_sex: set[SexOptions] = {sample.sex for sample in case.samples}
        return sample_sex.pop()

    @staticmethod
    def _get_normal_sample_id(case) -> str | None:
        for sample in case.samples:
            if not sample.is_tumour:
                return sample.internal_id

    @staticmethod
    def _get_tumor_sample_id(case) -> str:
        for sample in case.samples:
            if sample.is_tumour:
                return sample.internal_id
        raise BalsamicMissingTumorError(f"Case {case.internal_id} does not contain a tumor sample")

    def _resolve_bed_file(self, case, **flags) -> Path:
        bed_name = flags.get("panel_bed") or self._get_bed_name_from_lims(case)
        if db_bed := self.store.get_bed_version_by_short_name(bed_name):
            return Path(self.bed_directory, db_bed.filename)
        raise BedFileNotFoundError(f"No Bed file found for with provided name {bed_name}.")

    def _get_bed_name_from_lims(self, case: Case) -> str:
        """Get the bed name from LIMS. Assumes that all samples in the case have the same panel."""
        first_sample: Sample = case.samples[0]
        if lims_bed := self.lims_api.capture_kit(lims_id=first_sample.internal_id):
            return lims_bed
        else:
            raise BedFileNotFoundError(
                f"No bed file found in LIMS for sample {first_sample.internal_id} in for case {case.internal_id}."
            )

    def _get_pon_file(self, bed_file: Path) -> Path | None:
        """Finds the corresponding PON file for the given bed file.
        These are versioned and named like: <bed_file_name>_hg19_design_CNVkit_PON_reference_v<version>.cnn
        This method returns the latest version of the PON file matching the bed name.
        """
        identifier: str = bed_file.stem
        pattern: re.Pattern[str] = re.compile(rf"{re.escape(identifier)}.*_v(\d+)\.cnn$")
        candidates: list = []

        for file in self.pon_directory.glob("*.cnn"):
            if match := pattern.search(file.name):
                version = int(match[1])
                candidates.append((version, file))

        if not candidates:
            LOG.info(f"No PON file found for bed file {bed_file.name}. Configuring without PON.")
            return None
        _, latest_file = max(candidates, key=lambda x: x[0])

        return latest_file

    def _get_sample_config_path(self, case_id: str) -> Path:
        return Path(self.root_dir, case_id, f"{case_id}.json")

    def _ensure_required_config_files_exist(self, config: BalsamicCaseConfig) -> None:
        if not config.sample_config.exists():
            raise CaseNotConfiguredError(
                f"Please ensure that the config file {config.sample_config.exists()} exists."
            )

    def _get_coverage_pon(self, patient_sex: SexOptions) -> Path:
        return (
            self.gens_coverage_female_path
            if patient_sex == SexOptions.FEMALE
            else self.gens_coverage_male_path
        )
