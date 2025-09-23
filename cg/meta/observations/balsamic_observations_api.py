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
    BalsamicObservationPanels,
    BalsamicObservationsAnalysisTag,
    LoqusdbInstance,
)
from cg.constants.sequencing import SeqLibraryPrepCategory
from cg.exc import CaseNotFoundError, LoqusdbDuplicateRecordError
from cg.meta.observations.observations_api import ObservationsAPI
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.models.observations.input_files import BalsamicObservationsInputFiles
from cg.store.models import BedVersion, Case, Sample
from cg.utils.dict import get_full_path_dictionary
from tests.fixture_plugins.loqusdb_fixtures.loqusdb_api_fixtures import loqusdb_api

LOG = logging.getLogger(__name__)


class BalsamicObservationsAPI(ObservationsAPI):
    """API to manage Balsamic observations."""

    def __init__(self, config: CGConfig):
        self.analysis_api = BalsamicAnalysisAPI(config)
        super().__init__(config=config, analysis_api=self.analysis_api)
        # TODO maybe add loqusdb instances for panels or use get_loqusdb_api method
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
        prep_category: str = case.samples[0].prep_category
        if (
            prep_category == SeqLibraryPrepCategory.WHOLE_GENOME_SEQUENCING
            and self.analysis_api.is_analysis_normal_only(case.internal_id)
        ):
            LOG.error(
                f"Normal only analysis {case.internal_id} is not supported for WGS Loqusdb uploads"
            )
            return False
        elif (
            prep_category
            in [
                SeqLibraryPrepCategory.TARGETED_GENOME_SEQUENCING,
                SeqLibraryPrepCategory.WHOLE_EXOME_SEQUENCING,
            ]
            and len(case.samples) > 1
        ):
            LOG.error(
                f"Paired analysis {case.internal_id} is not supported for TGS Loqusdb uploads"
            )
            return False
        return True

    def is_case_eligible_for_observations_upload(self, case: Case) -> bool:
        """Return whether a cancer case is eligible for observations upload."""
        return all(
            [
                self.is_customer_eligible_for_observations_upload(case.customer.internal_id),
                self.is_sequencing_method_eligible_for_observations_upload(case.internal_id),
                self.is_analysis_type_eligible_for_observations_upload(case),
                self.is_sample_source_eligible_for_observations_upload(case.internal_id),
                self.is_panel_allowed_for_observations_upload(case),
            ]
        )

    def is_panel_allowed_for_observations_upload(self, case: Case) -> bool:
        """
        Returns True if WGS or TGS with the allowed panels.
        This assumes that all samples in the case have the same prep-category
        """
        sample: Sample = case.samples[0]
        if sample.prep_category in [
            SeqLibraryPrepCategory.TARGETED_GENOME_SEQUENCING,
            SeqLibraryPrepCategory.WHOLE_EXOME_SEQUENCING,
        ]:
            panel_short_name: str | None = self.lims_api.capture_kit(lims_id=sample.internal_id)
            bed_version: BedVersion | None = self.store.get_bed_version_by_short_name(
                panel_short_name
            )
            if not bed_version:
                LOG.warning(
                    f"No bed version found for LIMS panel {panel_short_name} for sample "
                    f"{sample.internal_id} in case {case.internal_id}"
                )
                return False
            if bed_version.bed.name not in list(BalsamicObservationPanels):
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
        self._upload_wgs_case(case)

    @staticmethod
    def _is_panel_upload(case: Case) -> bool:
        sample: Sample = case.samples[0]
        return sample.prep_category in [SeqLibraryPrepCategory.TARGETED_GENOME_SEQUENCING, SeqLibraryPrepCategory.WHOLE_EXOME_SEQUENCING]

    def _upload_panel_case(self, case: Case) -> None:
        bed_file_name: str = self.analysis_api.get_target_bed_from_lims(case.internal_id)
        bed_version: BedVersion | None = self.store.get_bed_version_by_file_name(bed_file_name)

        if not bed_version:
            return

        panel: str = bed_version.bed.name

        try:
            loqusdb_instance = LoqusdbInstance(panel)
            loqusdb_api: LoqusdbAPI = self.get_loqusdb_api(loqusdb_instance)



    def _upload_wgs_case(self, case: Case) -> None:
        loqusdb_upload_apis: list[LoqusdbAPI] = [
            self.loqusdb_somatic_api,
            self.loqusdb_tumor_api,
        ]  # TODO: Replace with if-statements
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
        # TODO: Check what should be done (get from somatic and set on the samples?)
        loqusdb_id: str = str(self.loqusdb_tumor_api.get_case(case_id=case.internal_id)[LOQUSDB_ID])
        self.update_statusdb_loqusdb_id(samples=case.samples, loqusdb_id=loqusdb_id)

    def load_cancer_observations(
        self, case: Case, input_files: BalsamicObservationsInputFiles, loqusdb_api: LoqusdbAPI
    ) -> None:
        """Load cancer observations to a specific Loqusdb API."""
        # TODO implement this logic for panel analyses
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
            sv_vcf_path: Path = input_files.sv_vcf_path  # TODO: NO SV upload for TGA
        else:
            LOG.info("Uploading germline observations to Loqusdb")
            snv_vcf_path: Path = input_files.snv_germline_vcf_path
            sv_vcf_path: Path = input_files.sv_germline_vcf_path if is_paired_analysis else None
            # TODO: NO SV upload for TGA

        load_output: dict = loqusdb_api.load(
            case_id=case.internal_id,
            snv_vcf_path=snv_vcf_path,
            sv_vcf_path=sv_vcf_path,
            qual_gq=True,
            gq_threshold=(  # TODO for the new uploads this value should be zero
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
        return BalsamicObservationsInputFiles(**get_full_path_dictionary(input_files))

    def delete_case(self, case_id: str) -> None:
        """Delete cancer case observations from Loqusdb."""
        case: Case = self.store.get_case_by_internal_id(internal_id=case_id)
        loqusdb_apis: list[LoqusdbAPI] = [self.loqusdb_somatic_api, self.loqusdb_tumor_api]
        for loqusdb_api in loqusdb_apis:
            if not loqusdb_api.get_case(case_id):
                LOG.error(f"Case {case_id} could not be found in Loqusdb. Skipping case deletion.")
                raise CaseNotFoundError
        for loqusdb_api in loqusdb_apis:
            loqusdb_api.delete_case(case_id)
        self.update_statusdb_loqusdb_id(samples=case.samples, loqusdb_id=None)
        LOG.info(f"Removed observations for case {case_id} from Loqusdb")
