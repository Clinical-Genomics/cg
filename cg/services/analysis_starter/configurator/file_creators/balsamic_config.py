import logging
import re
import subprocess
from pathlib import Path

from cg.apps.lims.api import LimsAPI
from cg.constants import SexOptions
from cg.constants.constants import GenomeVersion
from cg.constants.sequencing import SeqLibraryPrepCategory
from cg.exc import BalsamicMissingTumorError, BedFileNotFoundError
from cg.models.cg_config import BalsamicConfig
from cg.services.analysis_starter.configurator.models.balsamic import (
    BalsamicConfigInput,
    BalsamicConfigInputPanel,
    BalsamicConfigInputWGS,
)
from cg.store.models import Case, Sample
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class BalsamicConfigFileCreator:

    def __init__(self, cg_balsamic_config: BalsamicConfig, lims_api: LimsAPI, status_db: Store):
        self.status_db = status_db
        self.root_dir = cg_balsamic_config.root
        self.lims_api: LimsAPI = lims_api
        self.conda_binary: Path = cg_balsamic_config.conda_binary
        self.conda_env: str = cg_balsamic_config.conda_env
        self.balsamic_binary: Path = cg_balsamic_config.binary_path
        self.root_dir: Path = cg_balsamic_config.root
        self.bed_directory: Path = cg_balsamic_config.bed_path
        self.cache_dir: Path = cg_balsamic_config.balsamic_cache
        self.cadd_path: Path = cg_balsamic_config.cadd_path
        self.default_cluster_config: Path = cg_balsamic_config.cluster_config
        self.genome_interval_path: Path = cg_balsamic_config.genome_interval_path
        self.gens_coverage_female_path: Path = cg_balsamic_config.gens_coverage_female_path
        self.gens_coverage_male_path: Path = cg_balsamic_config.gens_coverage_male_path
        self.gnomad_af5_path: Path = cg_balsamic_config.gnomad_af5_path
        self.environment: str = cg_balsamic_config.conda_env
        self.sentieon_licence_path: Path = cg_balsamic_config.sentieon_licence_path
        self.sentieon_licence_server: str = cg_balsamic_config.sentieon_licence_server
        self.loqusdb_artefact_snv: Path = cg_balsamic_config.loqusdb_artefact_snv
        self.loqusdb_artefact_sv: Path = cg_balsamic_config.loqusdb_artefact_sv
        self.loqusdb_cancer_germline_snv: Path = cg_balsamic_config.loqusdb_cancer_germline_snv
        self.loqusdb_cancer_somatic_snv: Path = cg_balsamic_config.loqusdb_cancer_somatic_snv
        self.loqusdb_cancer_somatic_sv: Path = cg_balsamic_config.loqusdb_cancer_somatic_sv
        self.loqusdb_clinical_snv: Path = cg_balsamic_config.loqusdb_clinical_snv
        self.loqusdb_clinical_sv: Path = cg_balsamic_config.loqusdb_clinical_sv
        self.pon_directory: Path = cg_balsamic_config.pon_path
        self.slurm_account: str = cg_balsamic_config.slurm.account
        self.slurm_mail_user: str = cg_balsamic_config.slurm.mail_user
        self.swegen_snv: Path = cg_balsamic_config.swegen_snv
        self.swegen_sv: Path = cg_balsamic_config.swegen_sv

    def create(self, case_id: str, **flags) -> None:
        config_cli_input: BalsamicConfigInput = self._build_cli_input(case_id=case_id, **flags)
        self._create_config_file(config_cli_input)

    @staticmethod
    def _create_config_file(config_cli_input: BalsamicConfigInput) -> None:
        final_command: str = config_cli_input.dump_to_cli()
        LOG.debug(f"Running: {final_command}")
        subprocess.run(
            args=final_command,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def _build_cli_input(self, case_id, **flags) -> BalsamicConfigInput:
        case: Case = self.status_db.get_case_by_internal_id(
            case_id
        )  # TODO use strict version when available
        if self._all_samples_are_wgs(case):
            return self._build_wgs_config(case)
        else:
            return self._build_targeted_config(case, **flags)

    def _build_wgs_config(self, case: Case) -> BalsamicConfigInput:
        patient_sex: SexOptions = self._get_patient_sex(case)
        return BalsamicConfigInputWGS(
            analysis_dir=self.root_dir,
            analysis_workflow=case.data_analysis,  # TODO See if we can fix the typing in the data model
            artefact_snv_observations=self.loqusdb_artefact_snv,
            artefact_sv_observations=self.loqusdb_artefact_sv,
            balsamic_binary=self.balsamic_binary,
            balsamic_cache=self.cache_dir,
            cadd_annotations=self.cadd_path,
            cancer_germline_snv_observations=self.loqusdb_cancer_germline_snv,
            cancer_somatic_snv_observations=self.loqusdb_cancer_somatic_snv,
            cancer_somatic_sv_observations=self.loqusdb_cancer_somatic_sv,
            case_id=case.internal_id,
            clinical_snv_observations=self.loqusdb_clinical_snv,
            clinical_sv_observations=self.loqusdb_clinical_sv,
            conda_binary=self.conda_binary,
            conda_env=self.conda_env,
            fastq_path=Path(self.root_dir, case.internal_id, "fastq"),
            gender=patient_sex,
            genome_interval=self.genome_interval_path,
            genome_version=GenomeVersion.HG19,
            gens_coverage_pon=self._get_coverage_pon(patient_sex),
            gnomad_min_af5=self.gnomad_af5_path,
            normal_sample_name=self._get_normal_sample_id(case),
            sentieon_install_dir=self.sentieon_licence_path,
            sentieon_license=self.sentieon_licence_server,
            swegen_snv=self.swegen_snv,
            swegen_sv=self.swegen_sv,
            tumor_sample_name=self._get_tumor_sample_id(case),
        )

    def _build_targeted_config(self, case: Case, **flags) -> BalsamicConfigInput:
        bed_file: Path = self._resolve_bed_file(case, **flags)
        patient_sex: SexOptions = self._get_patient_sex(case)
        return BalsamicConfigInputPanel(
            analysis_dir=self.root_dir,
            analysis_workflow=case.data_analysis,  # TODO See if we can fix the typing in the data model
            artefact_snv_observations=self.loqusdb_artefact_snv,
            balsamic_binary=self.balsamic_binary,
            balsamic_cache=self.cache_dir,
            cadd_annotations=self.cadd_path,
            cancer_germline_snv_observations=self.loqusdb_cancer_germline_snv,
            cancer_somatic_snv_observations=self.loqusdb_cancer_somatic_snv,
            cancer_somatic_sv_observations=self.loqusdb_cancer_somatic_sv,
            case_id=case.internal_id,
            clinical_snv_observations=self.loqusdb_clinical_snv,
            clinical_sv_observations=self.loqusdb_clinical_sv,
            conda_binary=self.conda_binary,
            conda_env=self.conda_env,
            fastq_path=Path(self.root_dir, case.internal_id, "fastq"),
            gender=patient_sex,
            genome_version=GenomeVersion.HG19,
            gnomad_min_af5=self.gnomad_af5_path,
            normal_sample_name=self._get_normal_sample_id(case),
            panel_bed=bed_file,
            pon_cnn=self._get_pon_file(bed_file),
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
            sample.prep_category == SeqLibraryPrepCategory.WHOLE_GENOME_SEQUENCING
            for sample in case.samples
        )

    @staticmethod
    def _all_samples_are_exome(case: Case) -> bool:
        """Check if all samples in the case are exome."""
        return all(
            sample.prep_category == SeqLibraryPrepCategory.WHOLE_EXOME_SEQUENCING
            for sample in case.samples
        )

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
        if bed_version := self.status_db.get_bed_version_by_short_name(bed_name):
            return Path(self.bed_directory, bed_version.filename)
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
        # TODO: Discuss if we want to keep this logic or if we want to fetch this from servers
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

    def _get_coverage_pon(self, patient_sex: SexOptions) -> Path:
        return (
            self.gens_coverage_female_path
            if patient_sex == SexOptions.FEMALE
            else self.gens_coverage_male_path
        )
