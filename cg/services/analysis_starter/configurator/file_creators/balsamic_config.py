import logging
import subprocess
from pathlib import Path
from subprocess import CalledProcessError
from typing import cast

from pydantic import EmailStr

from cg.apps.lims.api import LimsAPI
from cg.constants import SexOptions
from cg.constants.constants import BedVersionGenomeVersion, GenomeVersion, Workflow
from cg.constants.process import EXIT_SUCCESS
from cg.constants.sequencing import SeqLibraryPrepCategory
from cg.models.cg_config import BalsamicConfig
from cg.services.analysis_starter.configurator.models.balsamic import (
    BalsamicConfigInput,
    BalsamicConfigInputPanel,
    BalsamicConfigInputWGS,
)
from cg.store.models import BedVersion, Case, Sample
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
        self.cache_version: str | None = cg_balsamic_config.cache_version
        self.cadd_path: Path = cg_balsamic_config.cadd_path
        self.genome_interval_path: Path = cg_balsamic_config.genome_interval_path
        self.gens_coverage_female_path: Path = cg_balsamic_config.gens_coverage_female_path
        self.gens_coverage_male_path: Path = cg_balsamic_config.gens_coverage_male_path
        self.gnomad_af5_path: Path = cg_balsamic_config.gnomad_af5_path
        self.environment: str = cg_balsamic_config.conda_env
        self.sentieon_licence_path: Path = cg_balsamic_config.sentieon_licence_path
        self.sentieon_licence_server: str = cg_balsamic_config.sentieon_licence_server
        self.loqusdb_artefact_snv: Path = cg_balsamic_config.loqusdb_dump_files.artefact_snv
        self.artefact_sv_observations: Path = cg_balsamic_config.loqusdb_dump_files.artefact_sv
        self.loqusdb_cancer_germline_snv: Path = (
            cg_balsamic_config.loqusdb_dump_files.cancer_germline_snv
        )
        self.loqusdb_cancer_somatic_snv: Path = (
            cg_balsamic_config.loqusdb_dump_files.cancer_somatic_snv
        )
        self.loqusdb_cancer_somatic_snv_panels: dict = (
            cg_balsamic_config.loqusdb_dump_files.cancer_somatic_snv_panels
        )
        self.loqusdb_cancer_somatic_sv: Path = (
            cg_balsamic_config.loqusdb_dump_files.cancer_somatic_sv
        )
        self.loqusdb_clinical_snv: Path = cg_balsamic_config.loqusdb_dump_files.clinical_snv
        self.loqusdb_clinical_sv: Path = cg_balsamic_config.loqusdb_dump_files.clinical_sv
        self.panel_of_normals: dict = cg_balsamic_config.panel_of_normals
        self.slurm_account: str = cg_balsamic_config.slurm.account
        self.slurm_mail_user: EmailStr = cg_balsamic_config.slurm.mail_user
        self.swegen_snv: Path = cg_balsamic_config.swegen_snv
        self.swegen_sv: Path = cg_balsamic_config.swegen_sv

    def create(self, case_id: str, fastq_path: Path, **flags) -> None:
        config_cli_input: BalsamicConfigInput = self._build_config_input(
            case_id=case_id, fastq_path=fastq_path, **flags
        )
        self._create_config_file(config_cli_input)

    @staticmethod
    def _create_config_file(config_cli_input: BalsamicConfigInput) -> None:
        final_command: str = config_cli_input.dump_to_cli()
        LOG.debug(f"Running: {final_command}")
        result = subprocess.run(
            args=final_command,
            shell=True,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if result.returncode != EXIT_SUCCESS:
            LOG.critical(result.stderr.decode("utf-8").rstrip())
            raise CalledProcessError(result.returncode, final_command)

    def _build_config_input(self, case_id: str, fastq_path: Path, **flags) -> BalsamicConfigInput:
        case: Case = self.status_db.get_case_by_internal_id_strict(case_id)
        if self._all_samples_are_wgs(case):
            return self._build_wgs_config(case=case, fastq_path=fastq_path)
        else:
            return self._build_targeted_config(
                case=case, fastq_path=fastq_path, override_panel_bed=flags.get("panel_bed")
            )

    def _build_wgs_config(self, case: Case, fastq_path: Path) -> BalsamicConfigInput:
        patient_sex: SexOptions = self._get_patient_sex(case)
        return BalsamicConfigInputWGS(
            analysis_dir=self.root_dir,
            analysis_workflow=cast(Workflow, case.data_analysis),
            artefact_snv_observations=self.loqusdb_artefact_snv,
            artefact_sv_observations=self.artefact_sv_observations,
            balsamic_binary=self.balsamic_binary,
            balsamic_cache=self.cache_dir,
            cache_version=self.cache_version,
            cadd_annotations=self.cadd_path,
            cancer_germline_snv_observations=self.loqusdb_cancer_germline_snv,
            cancer_somatic_snv_observations=self.loqusdb_cancer_somatic_snv,
            cancer_somatic_sv_observations=self.loqusdb_cancer_somatic_sv,
            case_id=case.internal_id,
            clinical_snv_observations=self.loqusdb_clinical_snv,
            clinical_sv_observations=self.loqusdb_clinical_sv,
            conda_binary=self.conda_binary,
            conda_env=self.conda_env,
            fastq_path=fastq_path,
            gender=patient_sex,
            genome_interval=self.genome_interval_path,
            genome_version=GenomeVersion.HG19,
            gens_coverage_pon=self._get_gens_coverage_pon_file(patient_sex),
            gnomad_min_af5=self.gnomad_af5_path,
            normal_sample_name=self._get_normal_sample_id_from_paired_analysis(case),
            sentieon_install_dir=self.sentieon_licence_path,
            sentieon_license=self.sentieon_licence_server,
            swegen_snv=self.swegen_snv,
            swegen_sv=self.swegen_sv,
            tumor_sample_name=self._get_tumor_or_single_sample_id(case),
        )

    def _build_targeted_config(
        self, case: Case, fastq_path: Path, override_panel_bed: str | None
    ) -> BalsamicConfigInput:
        bed_version: BedVersion = self._get_bed_version(
            case=case, override_panel_bed=override_panel_bed
        )
        bed_file: Path = Path(self.bed_directory, bed_version.filename)
        patient_sex: SexOptions = self._get_patient_sex(case)
        return BalsamicConfigInputPanel(
            analysis_dir=self.root_dir,
            analysis_workflow=cast(Workflow, case.data_analysis),
            artefact_snv_observations=self.loqusdb_artefact_snv,
            balsamic_binary=self.balsamic_binary,
            balsamic_cache=self.cache_dir,
            cache_version=self.cache_version,
            cadd_annotations=self.cadd_path,
            cancer_germline_snv_observations=self.loqusdb_cancer_germline_snv,
            cancer_somatic_snv_observations=self.loqusdb_cancer_somatic_snv,
            cancer_somatic_snv_panel_observations=self.loqusdb_cancer_somatic_snv_panels.get(
                bed_version.bed_name
            ),
            cancer_somatic_sv_observations=self.loqusdb_cancer_somatic_sv,
            case_id=case.internal_id,
            clinical_snv_observations=self.loqusdb_clinical_snv,
            clinical_sv_observations=self.loqusdb_clinical_sv,
            conda_binary=self.conda_binary,
            conda_env=self.conda_env,
            fastq_path=fastq_path,
            gender=patient_sex,
            genome_version=GenomeVersion.HG19,
            gnomad_min_af5=self.gnomad_af5_path,
            normal_sample_name=self._get_normal_sample_id_from_paired_analysis(case),
            panel_bed=bed_file,
            pon_cnn=self._get_pon_file(bed_version.shortname),
            exome=self._all_samples_are_exome(case),
            sentieon_install_dir=self.sentieon_licence_path,
            sentieon_license=self.sentieon_licence_server,
            soft_filter_normal=self._is_case_paired_analysis(case),
            swegen_snv=self.swegen_snv,
            swegen_sv=self.swegen_sv,
            tumor_sample_name=self._get_tumor_or_single_sample_id(case),
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
    def _get_normal_sample_id_from_paired_analysis(case) -> str | None:
        """Return the internal id of the normal sample if the case is a paired analysis, otherwise None."""
        if len(case.samples) == 2:
            for sample in case.samples:
                if not sample.is_tumour:
                    return sample.internal_id

    @staticmethod
    def _get_tumor_or_single_sample_id(case) -> str:
        """
        Return the internal id of the tumour sample if the case is a paired analysis,
        otherwise return the internal id of the single sample.
        """
        if len(case.samples) == 1:
            return case.samples[0].internal_id
        for sample in case.samples:
            if sample.is_tumour:
                return sample.internal_id

    @staticmethod
    def _is_case_paired_analysis(case: Case) -> bool:
        return len(case.samples) == 2

    def _get_bed_version(self, case: Case, override_panel_bed: str | None) -> BedVersion:
        first_sample: Sample = case.samples[0]
        short_name: str = override_panel_bed or self.lims_api.get_capture_kit_strict(
            first_sample.internal_id
        )
        return self.status_db.get_bed_version_by_short_name_and_genome_version_strict(
            short_name=short_name, genome_version=BedVersionGenomeVersion.HG19
        )

    def _get_pon_file(self, bed_short_name: str | None) -> Path | None:
        if pon_file := self.panel_of_normals.get(bed_short_name):
            return pon_file
        else:
            LOG.info(f"No PON file found for bed file {pon_file}. Configuring without PON.")
            return None

    def _get_sample_config_path(self, case_id: str) -> Path:
        return Path(self.root_dir, case_id, f"{case_id}.json")

    def _get_gens_coverage_pon_file(self, patient_sex: SexOptions) -> Path:
        """Return the corresponding PON file for WGS cases based on the patient's sex."""
        return (
            self.gens_coverage_male_path
            if patient_sex == SexOptions.MALE
            else self.gens_coverage_female_path
        )
