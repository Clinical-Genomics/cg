"""API for uploading Nallo observations."""

import logging

from housekeeper.store.models import File, Version

from cg.apps.loqus import LoqusdbAPI
from cg.constants.constants import CustomerId, SampleType
from cg.constants.observations import (
    LOQUSDB_ID,
    LOQUSDB_LONG_READ_CUSTOMERS,
    LOQUSDB_LONG_READ_SEQUENCING_METHODS,
    LoqusdbInstance,
    NalloLoadParameters,
    NalloObservationsAnalysisTag,
)
from cg.constants.sequencing import SeqLibraryPrepCategory
from cg.exc import CaseNotFoundError, LoqusdbDuplicateRecordError
from cg.meta.observations.observations_api import ObservationsAPI
from cg.meta.workflow.nallo import NalloAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.models.observations.input_files import NalloObservationsInputFiles
from cg.store.models import Case
from cg.utils.dict import get_full_path_dictionary

LOG = logging.getLogger(__name__)


class NalloObservationsAPI(ObservationsAPI):
    """API to manage Nallo observations."""

    def __init__(self, config: CGConfig):
        self.analysis_api = NalloAnalysisAPI(config)
        super().__init__(config=config, analysis_api=self.analysis_api)
        self.loqusdb_api: LoqusdbAPI = self.get_loqusdb_api(LoqusdbInstance.LWP)

    @property
    def loqusdb_customers(self) -> list[CustomerId]:
        """Customers that are eligible for RAREDISEASE Loqusdb uploads."""
        return LOQUSDB_LONG_READ_CUSTOMERS

    @property
    def loqusdb_sequencing_methods(self) -> list[str]:
        """Sequencing methods that are eligible for Loqusdb uploads."""
        return LOQUSDB_LONG_READ_SEQUENCING_METHODS

    @staticmethod
    def is_sample_type_eligible_for_observations_upload(case: Case) -> bool:
        """Return whether a Nallo case is free of tumor samples."""
        if case.tumour_samples:
            LOG.error(f"Sample type {SampleType.TUMOR} is not supported for Loqusdb uploads")
            return False
        return True

    def is_case_eligible_for_observations_upload(self, case: Case) -> bool:
        """Return whether a Nallo case is eligible for observations upload."""
        return all(
            [
                self.is_customer_eligible_for_observations_upload(case.customer.internal_id),
                self.is_sequencing_method_eligible_for_observations_upload(case.internal_id),
                self.is_sample_type_eligible_for_observations_upload(case),
                self.is_sample_source_eligible_for_observations_upload(case.internal_id),
            ]
        )

    def load_observations(self, case: Case) -> None:
        """
        Load observation counts to Loqusdb for a case.
        Raises:
            LoqusdbDuplicateRecordError: If case has already been uploaded.
        """
        input_files: NalloObservationsInputFiles = self.get_observations_input_files(case)
        if self.is_duplicate(
            case=case,
            loqusdb_api=self.loqusdb_api,
            profile_vcf_path=input_files.profile_vcf_path,
            profile_threshold=NalloLoadParameters.PROFILE_THRESHOLD.value,
        ):
            LOG.error(
                f"Case {case.internal_id} has already been uploaded to {repr(self.loqusdb_api)}"
            )
            raise LoqusdbDuplicateRecordError

        load_output: dict = self.loqusdb_api.load(
            case_id=case.internal_id,
            snv_vcf_path=input_files.snv_vcf_path,
            sv_vcf_path=input_files.sv_vcf_path,
            profile_vcf_path=input_files.profile_vcf_path,
            family_ped_path=input_files.family_ped_path,
            gq_threshold=NalloLoadParameters.GQ_THRESHOLD.value,
            hard_threshold=NalloLoadParameters.HARD_THRESHOLD.value,
            soft_threshold=NalloLoadParameters.SOFT_THRESHOLD.value,
            snv_gq_only=NalloLoadParameters.SNV_GQ_ONLY.value,
            loqusdb_options=["--keep-chr-prefix", "--genome-build", "GRCh38"],
        )
        loqusdb_id = str(self.loqusdb_api.get_case(case_id=case.internal_id)[LOQUSDB_ID])
        self.update_statusdb_loqusdb_id(samples=case.samples, loqusdb_id=loqusdb_id)
        LOG.info(f"Uploaded {load_output['variants']} variants to {repr(self.loqusdb_api)}")

    def get_observations_files_from_hk(
        self, hk_version: Version, case_id: str
    ) -> NalloObservationsInputFiles:
        """Return observations files given a Housekeeper version for Nallo."""
        input_files: dict[str, File] = {
            "snv_vcf_path": self.housekeeper_api.files(
                version=hk_version.id, tags=[NalloObservationsAnalysisTag.SNV_VCF]
            ).first(),
            "sv_vcf_path": (
                self.housekeeper_api.files(
                    version=hk_version.id, tags=[NalloObservationsAnalysisTag.SV_VCF]
                ).first()
                if self.analysis_api.get_data_analysis_type(case_id)
                == SeqLibraryPrepCategory.WHOLE_GENOME_SEQUENCING
                else None
            ),
            "profile_vcf_path": self.housekeeper_api.files(
                version=hk_version.id, tags=[NalloObservationsAnalysisTag.SNV_VCF]
            ).first(),
            "family_ped_path": self.housekeeper_api.files(
                version=hk_version.id, tags=[NalloObservationsAnalysisTag.FAMILY_PED]
            ).first(),
        }
        return NalloObservationsInputFiles(**get_full_path_dictionary(input_files))

    def delete_case(self, case_id: str) -> None:
        """Delete Nallo case observations from Loqusdb."""
        case: Case = self.store.get_case_by_internal_id(internal_id=case_id)
        if not self.loqusdb_api.get_case(case_id):
            LOG.error(f"Case {case_id} could not be found in Loqusdb. Skipping case deletion.")
            raise CaseNotFoundError
        self.loqusdb_api.delete_case(case_id)
        self.update_statusdb_loqusdb_id(samples=case.samples, loqusdb_id=None)
        LOG.info(f"Removed observations for case {case_id} from {repr(self.loqusdb_api)}")
