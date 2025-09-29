"""API for uploading cancer observations."""

import logging
from pathlib import Path

from housekeeper.store.models import File, Version

from cg.apps.loqus import LoqusdbAPI
from cg.constants.constants import CancerAnalysisType, CustomerId
from cg.constants.observations import (
    LOQUSDB_CANCER_CUSTOMERS,
    LOQUSDB_CANCER_SEQUENCING_METHODS,
    LOQUSDB_ID,
    BalsamicLoadParameters,
    BalsamicObservationPanel,
    BalsamicObservationsAnalysisTag,
    LoqusdbInstance,
)
from cg.constants.sequencing import SeqLibraryPrepCategory
from cg.exc import CaseNotFoundError, LoqusdbDeleteCaseError, LoqusdbDuplicateRecordError
from cg.meta.observations.observations_api import ObservationsAPI
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.models.observations.input_files import BalsamicObservationsInputFiles
from cg.store.models import BedVersion, Case, Sample
from cg.utils.dict import get_full_path_dictionary

LOG = logging.getLogger(__name__)

PANEL_TO_LOQUSDB_INSTANCE_MAP: dict = {
    BalsamicObservationPanel.LYMPHOID: LoqusdbInstance.SOMATIC_LYMPHOID,
    BalsamicObservationPanel.MYELOID: LoqusdbInstance.SOMATIC_MYELOID,
    BalsamicObservationPanel.EXOME: LoqusdbInstance.SOMATIC_EXOME,
}


class BalsamicObservationsAPI(ObservationsAPI):
    """API to manage Balsamic observations."""

    def __init__(self, config: CGConfig):
        self.analysis_api = BalsamicAnalysisAPI(config)
        super().__init__(config=config, analysis_api=self.analysis_api)
        self.lims_api = config.lims_api
        self.loqusdb_somatic_api: LoqusdbAPI = self.get_loqusdb_api(LoqusdbInstance.SOMATIC)
        self.loqusdb_tumor_api: LoqusdbAPI = self.get_loqusdb_api(LoqusdbInstance.TUMOR)

    @property
    def loqusdb_customers(self) -> list[CustomerId]:
        """Customers that are eligible for cancer Loqusdb uploads."""
        return LOQUSDB_CANCER_CUSTOMERS

    @property
    def loqusdb_sequencing_methods(self) -> list[str]:
        """Return sequencing methods that are eligible for cancer Loqusdb uploads."""
        return LOQUSDB_CANCER_SEQUENCING_METHODS

    def is_analysis_type_eligible_for_observations_upload(self, case: Case) -> bool:
        """Return whether the cancer analysis type is eligible for cancer Loqusdb uploads."""
        if self.analysis_api.is_analysis_normal_only(case.internal_id):
            LOG.error(
                f"Normal only analysis {case.internal_id} is not supported for Loqusdb uploads"
            )
            return False
        prep_category: str = case.samples[0].prep_category
        if prep_category in [
            SeqLibraryPrepCategory.TARGETED_GENOME_SEQUENCING,
            SeqLibraryPrepCategory.WHOLE_EXOME_SEQUENCING,
        ] and self._is_paired_analysis(case):
            LOG.error(
                f"Paired analysis {case.internal_id} is not supported for TGS Loqusdb uploads"
            )
            return False
        return True

    @staticmethod
    def _is_paired_analysis(case: Case) -> bool:
        return len(case.samples) > 1

    def is_case_eligible_for_observations_upload(self, case: Case) -> bool:
        """Return whether a cancer case is eligible for observations upload."""
        return all(
            [
                self.is_customer_eligible_for_observations_upload(case.customer.internal_id),
                self.is_analysis_type_eligible_for_observations_upload(case),
                self.is_sample_source_type_ffpe(case.internal_id),
                self.is_panel_allowed_for_observations_upload(case),
            ]
        )

    def is_panel_allowed_for_observations_upload(self, case: Case) -> bool:
        """
        True if WGS.
        If TGS/WES, True for panels with LoqusDB instances.
        This assumes that all samples in the case have the same prep-category.
        """
        if self._is_panel_upload(case):
            sample: Sample = case.samples[0]
            panel_short_name: str | None = self.lims_api.capture_kit(sample.internal_id)
            bed_version: BedVersion | None = self.store.get_bed_version_by_short_name(
                panel_short_name
            )
            if not bed_version:
                LOG.warning(
                    f"No bed version found for LIMS panel {panel_short_name} for sample "
                    f"{sample.internal_id} in case {case.internal_id}"
                )
                return False
            if bed_version.bed.name not in list(BalsamicObservationPanel):
                return False
        return True

    def load_observations(self, case: Case) -> None:
        """
        Upload observation counts to Loqusdb for a Balsamic case.

        Raises:
            LoqusdbDuplicateRecordError: If case has already been uploaded.
        """
        if self._is_panel_upload(case):
            self._upload_panel_case(case)
        else:
            self._upload_wgs_case(case)

    @staticmethod
    def _is_panel_upload(case: Case) -> bool:
        sample: Sample = case.samples[0]
        return sample.prep_category in [
            SeqLibraryPrepCategory.TARGETED_GENOME_SEQUENCING,
            SeqLibraryPrepCategory.WHOLE_EXOME_SEQUENCING,
        ]

    def _upload_panel_case(self, case: Case) -> None:
        """
        Uploads the case to one of the somatic panel LoqusDB instances. The case is known to have
        a panel with a known LoqusDB instance.
        """
        loqusdb_api: LoqusdbAPI = self._get_panel_loqusdb_api(case)
        if self.is_duplicate(case=case, loqusdb_api=loqusdb_api):
            LOG.error(f"Case {case.internal_id} has already been uploaded to Loqusdb")
            raise LoqusdbDuplicateRecordError
        input_files: BalsamicObservationsInputFiles = self.get_observations_input_files(case)
        loqusdb_api.load(
            case_id=case.internal_id,
            snv_vcf_path=input_files.snv_vcf_path,
        )
        loqusdb_id: str = str(loqusdb_api.get_case(case_id=case.internal_id)[LOQUSDB_ID])
        self.update_statusdb_loqusdb_id(samples=case.samples, loqusdb_id=loqusdb_id)

    def _get_panel_loqusdb_api(self, case: Case) -> LoqusdbAPI:
        sample: Sample = case.samples[0]
        bed_short_name: str = self.lims_api.capture_kit(sample.internal_id)
        bed_version: BedVersion = self.store.get_bed_version_by_short_name_strict(bed_short_name)
        panel: str = bed_version.bed.name
        loqusdb_instance: LoqusdbInstance = PANEL_TO_LOQUSDB_INSTANCE_MAP[
            BalsamicObservationPanel(panel)
        ]
        return self.get_loqusdb_api(loqusdb_instance)

    def _upload_wgs_case(self, case: Case) -> None:
        loqusdb_upload_apis: list[LoqusdbAPI] = [
            self.loqusdb_somatic_api,
            self.loqusdb_tumor_api,
        ]
        for loqusdb_api in loqusdb_upload_apis:
            if self.is_duplicate(case=case, loqusdb_api=loqusdb_api):
                LOG.error(f"Case {case.internal_id} has already been uploaded to Loqusdb")
                raise LoqusdbDuplicateRecordError
        input_files: BalsamicObservationsInputFiles = self.get_observations_input_files(case)
        for loqusdb_api in loqusdb_upload_apis:
            self.load_cancer_observations(
                case=case, input_files=input_files, loqusdb_api=loqusdb_api
            )
        # Update Statusdb with a germline Loqusdb ID
        loqusdb_id: str = str(self.loqusdb_tumor_api.get_case(case_id=case.internal_id)[LOQUSDB_ID])
        self.update_statusdb_loqusdb_id(samples=case.samples, loqusdb_id=loqusdb_id)

    def load_cancer_observations(
        self, case: Case, input_files: BalsamicObservationsInputFiles, loqusdb_api: LoqusdbAPI
    ) -> None:
        """Load cancer observations to a specific Loqusdb API."""
        is_somatic_db: bool = LoqusdbInstance.SOMATIC in str(loqusdb_api.config_path)
        is_paired_analysis: bool = (
            CancerAnalysisType.TUMOR_NORMAL
            in self.analysis_api.get_data_analysis_type(case.internal_id)
        )
        if is_somatic_db:
            if not is_paired_analysis:
                return
            LOG.info("Uploading somatic observations to Loqusdb")
            snv_vcf_path: Path = input_files.snv_vcf_path
            sv_vcf_path: Path = input_files.sv_vcf_path
        else:
            LOG.info("Uploading germline observations to Loqusdb")
            snv_vcf_path: Path = input_files.snv_germline_vcf_path
            sv_vcf_path: Path = input_files.sv_germline_vcf_path if is_paired_analysis else None

        load_output: dict = loqusdb_api.load(
            case_id=case.internal_id,
            snv_vcf_path=snv_vcf_path,
            sv_vcf_path=sv_vcf_path,
            qual_gq=True,
            gq_threshold=(
                BalsamicLoadParameters.QUAL_THRESHOLD.value
                if is_somatic_db
                else BalsamicLoadParameters.QUAL_GERMLINE_THRESHOLD.value
            ),
        )
        LOG.info(f"Uploaded {load_output['variants']} variants to {repr(loqusdb_api)}")

    def get_observations_files_from_hk(
        self, hk_version: Version, case_id: str = None
    ) -> BalsamicObservationsInputFiles:
        """Return observations files given a Housekeeper version for cancer."""
        input_files: dict[str, File] = {
            "snv_germline_vcf_path": self.housekeeper_api.files(
                version=hk_version.id, tags=[BalsamicObservationsAnalysisTag.SNV_GERMLINE_VCF]
            ).first(),
            "snv_vcf_path": self.housekeeper_api.files(
                version=hk_version.id, tags=[BalsamicObservationsAnalysisTag.SNV_VCF]
            ).first(),
            "sv_germline_vcf_path": self.housekeeper_api.files(
                version=hk_version.id, tags=[BalsamicObservationsAnalysisTag.SV_GERMLINE_VCF]
            ).first(),
            "sv_vcf_path": self.housekeeper_api.files(
                version=hk_version.id, tags=[BalsamicObservationsAnalysisTag.SV_VCF]
            ).first(),
        }
        return BalsamicObservationsInputFiles.model_validate(get_full_path_dictionary(input_files))

    def delete_case(self, case_id: str) -> None:
        """Delete cancer case observations from Loqusdb."""
        case: Case = self.store.get_case_by_internal_id(internal_id=case_id)
        loqusdb_apis: list[LoqusdbAPI] = self._get_relevant_loqusdb_apis(case)
        for loqusdb_api in loqusdb_apis:
            if not loqusdb_api.get_case(case_id):
                LOG.error(f"Case {case_id} could not be found in Loqusdb. Skipping case deletion.")
                raise CaseNotFoundError
        for loqusdb_api in loqusdb_apis:
            loqusdb_api.delete_case(case_id)
        self.update_statusdb_loqusdb_id(samples=case.samples, loqusdb_id=None)
        LOG.info(f"Removed observations for case {case_id} from Loqusdb")

    def _get_relevant_loqusdb_apis(self, case: Case) -> list[LoqusdbAPI]:
        if not self._is_panel_upload(case):
            return [self.loqusdb_somatic_api, self.loqusdb_tumor_api]
        try:
            return [self._get_panel_loqusdb_api(case)]
        except ValueError as error:
            raise LoqusdbDeleteCaseError from error
