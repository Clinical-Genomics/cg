import logging
import re
import subprocess
from pathlib import Path

from cg.apps.lims import LimsAPI
from cg.constants import SexOptions
from cg.constants.constants import GenomeVersion
from cg.constants.sequencing import SeqLibraryPrepCategory
from cg.exc import (
    BalsamicInconsistentSexError,
    BalsamicMissingTumorError,
    BedFileNotFoundError,
    CaseNotConfiguredError,
)
from cg.meta.workflow.fastq import BalsamicFastqHandler
from cg.models.cg_config import BalsamicConfig
from cg.services.analysis_starter.configurator.configurator import Configurator
from cg.services.analysis_starter.configurator.models.balsamic import (
    BalsamicCaseConfig,
    BalsamicConfigInput,
)
from cg.store.models import Case
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class BalsamicConfigurator(Configurator):
    def __init__(
        self,
        config: BalsamicConfig,
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
        self.loqusdb_cancer_germline_snv: Path = config.loqusdb_cancer_germline_snv
        self.loqusdb_cancer_germline_sv: Path = config.loqusdb_cancer_germline_sv
        self.loqusdb_cancer_somatic_snv: Path = config.loqusdb_cancer_somatic_snv
        self.loqusdb_cancer_somatic_sv: Path = config.loqusdb_cancer_somatic_sv
        self.loqusdb_clinical_snv: Path = config.loqusdb_clinical_snv
        self.loqusdb_clinical_sv: Path = config.loqusdb_clinical_sv
        self.pon_directory: Path = Path(config.pon_path)
        self.slurm_account: str = config.slurm.account
        self.slurm_mail_user: str = config.slurm.mail_user
        self.swegen_snv: Path = config.swegen_snv
        self.swegen_sv: Path = config.swegen_sv

    def configure(self, case_id: str, **flags) -> BalsamicCaseConfig:
        LOG.info(f"Configuring case {case_id}")
        self.fastq_handler.link_fastq_files(case_id)
        config_cli_input: BalsamicConfigInput = self._build_cli_input(case_id)
        self.create_config_file(config_cli_input)
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
            qos=self.store.get_case_by_internal_id(case_id).slurm_priority,
            sample_config=self._get_sample_config_path(case_id),
        )
        balsamic_config: BalsamicCaseConfig = self._set_flags(config=balsamic_config, **flags)
        self._ensure_valid_config(balsamic_config)
        return balsamic_config

    @staticmethod
    def create_config_file(config_cli_input: BalsamicConfigInput) -> None:
        final_command: str = config_cli_input.dump_to_cli()
        LOG.debug(f"Running: {final_command}")
        subprocess.run(
            args=final_command,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def _build_cli_input(self, case_id) -> BalsamicConfigInput:
        case: Case = self.store.get_case_by_internal_id(case_id)
        if self._all_samples_are_wgs(case):
            return self._build_wgs_config(case)
        else:
            return self._build_targeted_config(case)

    def _build_wgs_config(self, case: Case) -> BalsamicConfigInput:
        patient_sex: SexOptions = self._get_patient_sex(case)
        return BalsamicConfigInput(
            analysis_dir=self.root_dir,
            analysis_workflow=case.data_analysis,
            artefact_snv_observations=self.loqusdb_artefact_snv,
            balsamic_binary=self.balsamic_binary,
            balsamic_cache=self.cache_dir,
            cadd_annotations=self.cadd_path,
            cancer_germline_snv_observations=self.loqusdb_cancer_germline_snv,
            cancer_germline_sv_observations=self.loqusdb_cancer_germline_sv,
            cancer_somatic_snv_observations=self.loqusdb_cancer_somatic_snv,
            cancer_somatic_sv_observations=self.loqusdb_cancer_somatic_sv,
            case_id=case.internal_id,
            clinical_snv_observations=self.loqusdb_clinical_snv,
            clinical_sv_observations=self.loqusdb_clinical_sv,
            conda_binary=self.conda_binary,
            fastq_path=Path(self.root_dir, case.internal_id, "fastq"),
            gender=patient_sex,
            genome_interval=self.genome_interval_path,
            genome_version=GenomeVersion.HG19,
            gens_coverage_pon=(
                self.gens_coverage_female_path
                if patient_sex == SexOptions.FEMALE
                else self.gens_coverage_male_path
            ),
            gnomad_min_af5=self.gnomad_af5_path,
            normal_sample_name=self._get_normal_sample_id(case),
            sentieon_install_dir=self.sentieon_licence_path,
            sentieon_license=self.sentieon_licence_server,
            swegen_snv=self.swegen_snv,
            swegen_sv=self.swegen_sv,
            tumor_sample_name=self._get_tumor_sample_id(case),
        )

    def _build_targeted_config(self, case, **flags) -> BalsamicConfigInput:
        bed_file: Path = self._resolve_bed_file(case, **flags)
        patient_sex: SexOptions = self._get_patient_sex(case)
        return BalsamicConfigInput(
            analysis_dir=self.root_dir,
            analysis_workflow=case.data_analysis,
            artefact_snv_observations=self.loqusdb_artefact_snv,
            balsamic_binary=self.balsamic_binary,
            balsamic_cache=self.cache_dir,
            cadd_annotations=self.cadd_path,
            cancer_germline_snv_observations=self.loqusdb_cancer_germline_snv,
            cancer_germline_sv_observations=self.loqusdb_cancer_germline_sv,
            cancer_somatic_snv_observations=self.loqusdb_cancer_somatic_snv,
            cancer_somatic_sv_observations=self.loqusdb_cancer_somatic_sv,
            case_id=case.internal_id,
            clinical_snv_observations=self.loqusdb_clinical_snv,
            clinical_sv_observations=self.loqusdb_clinical_sv,
            conda_binary=self.conda_binary,
            fastq_path=Path(self.root_dir, case.internal_id, "fastq"),
            gender=patient_sex,
            genome_version=GenomeVersion.HG19,
            gnomad_min_af5=self.gnomad_af5_path,
            normal_sample_name=self._get_normal_sample_id(case),
            panel_bed=bed_file,
            pon_cnn=self._get_pon(bed_file),
            exome=self._all_samples_are_exome(case),
            sentieon_install_dir=self.sentieon_licence_path,
            sentieon_license=self.sentieon_licence_server,
            soft_filter_normal=bool(self._get_normal_sample_id(case)),
            swegen_snv=self.swegen_snv,
            swegen_sv=self.swegen_sv,
            tumor_sample_name=self._get_tumor_sample_id(case),
        )

    @staticmethod
    def _all_samples_are_wgs(case: Case) -> bool:
        """Check if all samples in the case are WGS."""
        return all(
            sample.application_version.application.prep_category
            == SeqLibraryPrepCategory.WHOLE_GENOME_SEQUENCING
            for sample in case.samples
        )

    @staticmethod
    def _all_samples_are_exome(case: Case) -> bool:
        """Check if all samples in the case are exome."""
        return all(
            sample.application_version.application.prep_category
            == SeqLibraryPrepCategory.WHOLE_EXOME_SEQUENCING
            for sample in case.samples
        )

    @staticmethod
    def _get_patient_sex(case) -> SexOptions:
        sample_sex: set[SexOptions] = {sample.sex for sample in case.samples}
        if len(sample_sex) == 1:
            return sample_sex.pop()
        else:
            raise BalsamicInconsistentSexError(
                f"Case {case.internal_id} contains samples of differing sex"
            )

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
        first_sample = case.samples[0]
        if lims_bed := self.lims_api.capture_kit(lims_id=first_sample.internal_id):
            return lims_bed
        else:
            raise BedFileNotFoundError(
                f"No bed file found in LIMS for sample {first_sample.internal_id} in for case {case.internal_id}."
            )

    def _get_pon(self, bed_file: Path) -> Path:
        """Finds the corresponding PON file for the given bed file.
        These are versioned and named like: <bed_file_name>_hg19_design_CNVkit_PON_reference_v<version>.cnn
        This method returns the latest version of the PON file matching the bed name.
        """
        identifier = bed_file.stem
        pattern = re.compile(rf"{re.escape(identifier)}.*_v(\d+)\.cnn$")
        candidates = []

        for file in self.pon_directory.glob("*.cnn"):
            if match := pattern.search(file.name):
                version = int(match[1])
                candidates.append((version, file))

        if not candidates:
            raise FileNotFoundError(
                f"No matching CNN files found for identifier '{identifier}' in {self.pon_directory}"
            )

        return max(candidates, key=lambda x: x[0])[1]

    def _get_sample_config_path(self, case_id: str) -> Path:
        return Path(self.root_dir, case_id, f"{case_id}.json")

    @staticmethod
    def _ensure_valid_config(config: BalsamicCaseConfig) -> None:
        if not config.sample_config.exists():
            raise CaseNotConfiguredError(
                f"Please ensure that the config file {config.sample_config.exists()} exists."
            )
