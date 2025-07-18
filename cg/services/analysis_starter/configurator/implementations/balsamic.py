import re
from pathlib import Path

from cg.apps.lims import LimsAPI
from cg.constants import SexOptions
from cg.constants.constants import GenomeVersion
from cg.constants.sequencing import SeqLibraryPrepCategory
from cg.exc import BalsamicInconsistentSexError, BalsamicMissingTumorError, BedFileNotFound
from cg.models.cg_config import BalsamicConfig
from cg.services.analysis_starter.configurator.abstract_model import CaseConfig
from cg.services.analysis_starter.configurator.configurator import Configurator
from cg.services.analysis_starter.configurator.models.balsamic import BalsamicConfigInput
from cg.store.models import Case
from cg.store.store import Store


class VariantType:
    SNV = "snv"
    SV = "sv"


class ObservationsFilePatterns:
    """File patterns regarding dump Loqusdb files."""

    ARTEFACT_SNV = "artefact_somatic_snv"
    CLINICAL_SNV = "clinical_snv"
    CLINICAL_SV = "clinical_sv"
    CANCER_GERMLINE_SNV = "cancer_germline_snv"
    CANCER_GERMLINE_SV = "cancer_germline_sv"
    CANCER_SOMATIC_SNV = "cancer_somatic_snv"
    CANCER_SOMATIC_SV = "cancer_somatic_sv"


class BalsamicConfigurator(Configurator):
    def __init__(self, config: BalsamicConfig, lims_api: LimsAPI, store: Store):
        self.store: Store = store
        self.lims_api: LimsAPI = lims_api
        self.root_dir: str = config.root
        self.bed_directory: str = config.balsamic.bed_directory
        self.cache_dir: str = config.balsamic_cache
        self.cadd_path: str = config.balsamic.cadd_path
        self.genome_interval_path: str = config.balsamic.genome_interval_path
        self.gens_coverage_female_path: str = config.balsamic.gens_coverage_female_path
        self.gens_coverage_male_path: str = config.balsamic.gens_coverage_male_path
        self.gnomad_af5_path: str = config.balsamic.gnomad_af5_path
        self.sentieon_licence_path: str = config.balsamic.sentieon_licence_path
        self.sentieon_licence_server: str = config.sentieon_licence_server
        self.loqusdb_artefact_snv: str = config.loqusdb_artefact_snv
        self.loqusdb_cancer_germline_snv: str = config.loqusdb_cancer_germline_snv
        self.loqusdb_cancer_germline_sv: str = config.loqusdb_cancer_germline_sv
        self.loqusdb_cancer_somatic_snv: str = config.loqusdb_cancer_somatic_snv
        self.loqusdb_cancer_somatic_sv: str = config.loqusdb_cancer_somatic_sv
        self.loqusdb_clinical_snv: str = config.loqusdb_clinical_snv
        self.loqusdb_clinical_sv: str = config.loqusdb_clinical_sv
        self.ponn_directory: Path = Path(config.balsamic.ponn_directory)
        self.swen_snv: str = config.swegen_snv
        self.swen_sv: str = config.swegen_sv

    def configure(self, case_id: str, **flags) -> CaseConfig:
        config_cli_input: BalsamicConfigInput = self._build_cli_input(case_id)
        self.create_config_file(config_cli_input)
        return self.get_config(case_id=case_id, **flags)

    def get_config(self, case_id: str, **flags) -> CaseConfig:
        pass

    def _ensure_valid_config(self, config: CaseConfig) -> None:
        pass

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
            balsamic_cache=self.cache_dir,
            cadd_annotations=self.cadd_path,
            cancer_germline_snv_observations=self.loqusdb_cancer_germline_snv,
            cancer_germline_sv_observations=self.loqusdb_cancer_germline_sv,
            cancer_somatic_snv_observations=self.loqusdb_cancer_somatic_snv,
            cancer_somatic_sv_observations=self.loqusdb_cancer_somatic_sv,
            case_id=case.internal_id,
            clinical_snv_observations=self.loqusdb_clinical_snv,
            clinical_sv_observations=self.loqusdb_clinical_sv,
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
            swegen_snv=self.swen_snv,
            swegen_sv=self.swen_sv,
            tumor_sample_name=self._get_tumor_sample_id(case),
        )

    def _build_targeted_config(self, case, **flags) -> BalsamicConfigInput:
        bed_file: Path = self._resolve_bed_file(case, **flags)
        patient_sex: SexOptions = self._get_patient_sex(case)
        return BalsamicConfigInput(
            analysis_dir=self.root_dir,
            analysis_workflow=case.data_analysis,
            artefact_snv_observations=self.loqusdb_artefact_snv,
            balsamic_cache=self.cache_dir,
            cadd_annotations=self.cadd_path,
            cancer_germline_snv_observations=self.loqusdb_cancer_germline_snv,
            cancer_germline_sv_observations=self.loqusdb_cancer_germline_sv,
            cancer_somatic_snv_observations=self.loqusdb_cancer_somatic_snv,
            cancer_somatic_sv_observations=self.loqusdb_cancer_somatic_sv,
            case_id=case.internal_id,
            clinical_snv_observations=self.loqusdb_clinical_snv,
            clinical_sv_observations=self.loqusdb_clinical_sv,
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
            swegen_snv=self.swen_snv,
            swegen_sv=self.swen_sv,
            tumor_sample_name=self._get_tumor_sample_id(case),
        )

    def create_config_file(self, config_cli_input: BalsamicConfigInput) -> Path:
        pass

    @staticmethod
    def _all_samples_are_wgs(case: Case) -> bool:
        """Check if all samples in the case are WGS."""
        return all(
            sample.application_version.application.prep_category
            == SeqLibraryPrepCategory.WHOLE_GENOME_SEQUENCING
            for sample in case.samples
        )

    @staticmethod
    def _get_patient_sex(case):
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
        raise BedFileNotFound(f"No Bed file found for the provided name {bed_name}.")

    def _get_bed_name_from_lims(self, case: Case) -> str:
        """Get the bed name from LIMS. Assumes that all samples in the case have the same panel."""
        first_sample = case.samples[0]
        if lims_bed := self.lims_api.capture_kit(lims_id=first_sample.internal_id):
            return lims_bed
        else:
            raise BedFileNotFound(
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

        for file in self.ponn_directory.glob("*.cnn"):
            if match := pattern.search(file.name):
                version = int(match[1])
                candidates.append((version, file))

        if not candidates:
            raise FileNotFoundError(
                f"No matching CNN files found for identifier '{identifier}' in {self.ponn_directory}"
            )

        return max(candidates, key=lambda x: x[0])[1]

    @staticmethod
    def _all_samples_are_exome(case: Case) -> bool:
        """Check if all samples in the case are exome."""
        return all(
            sample.application_version.application.prep_category
            == SeqLibraryPrepCategory.WHOLE_EXOME_SEQUENCING
            for sample in case.samples
        )
