"""API for uploading rare disease observations."""

import logging

from housekeeper.store.models import File, Version

from cg.apps.loqus import LoqusdbAPI
from cg.constants.constants import CustomerId, SampleType
from cg.constants.observations import (
    LOQSUDB_RARE_DISEASE_CUSTOMERS,
    LOQUSDB_ID,
    LOQUSDB_RARE_DISEASE_SEQUENCING_METHODS,
    LoqusdbInstance,
    MipDNALoadParameters,
    MipDNAObservationsAnalysisTag,
)
from cg.constants.sample_sources import SourceType
from cg.constants.sequencing import SequencingMethod
from cg.exc import (
    CaseNotFoundError,
    LoqusdbDuplicateRecordError,
    LoqusdbUploadCaseError,
)
from cg.meta.observations.observations_api import ObservationsAPI
from cg.meta.workflow.mip_dna import MipDNAAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.models.observations.input_files import MipDNAObservationsInputFiles
from cg.store.models import Case
from cg.utils.dict import get_full_path_dictionary

LOG = logging.getLogger(__name__)


class MipDNAObservationsAPI(ObservationsAPI):
    """API to manage MIP-DNA observations."""

    def __init__(self, config: CGConfig):
        self.analysis_api = MipDNAAnalysisAPI(config)
        super().__init__(config=config, analysis_api=self.analysis_api)
        self.loqusdb_wes_api: LoqusdbAPI = self.get_loqusdb_api(LoqusdbInstance.WES)
        self.loqusdb_wgs_api: LoqusdbAPI = self.get_loqusdb_api(LoqusdbInstance.WGS)

    def get_loqusdb_customers(self) -> list[CustomerId]:
        """Return customers that are eligible for rare disease Loqusdb uploads."""
        return LOQSUDB_RARE_DISEASE_CUSTOMERS

    def get_loqusdb_sequencing_methods(self) -> list[str]:
        """Return sequencing methods that are eligible for cancer Loqusdb uploads."""
        return LOQUSDB_RARE_DISEASE_SEQUENCING_METHODS

    @staticmethod
    def is_sample_type_eligible_for_observations_upload(case: Case) -> bool:
        """Return whether a rare disease case is free of tumor samples."""
        if case.tumour_samples:
            LOG.error(f"Sample type {SampleType.TUMOR} is not supported for Loqusdb uploads")
            return False
        return True

    def is_sample_source_eligible_for_observations_upload(self, case_id: str) -> bool:
        """Check if the sample source is FFPE."""
        source_type: str | None = self.analysis_api.get_case_source_type(case_id)
        if source_type and SourceType.FFPE.lower() not in source_type.lower():
            return True
        LOG.error(f"Source type {source_type} is not supported for Loqusdb uploads")
        return False

    def is_case_eligible_for_observations_upload(self, case: Case) -> bool:
        """Return whether a rare disease case is eligible for observations upload."""
        is_customer_eligible_for_observations_upload: bool = (
            self.is_customer_eligible_for_observations_upload(case.customer.internal_id)
        )
        is_sequencing_method_eligible_for_observations_upload: bool = (
            self.is_sequencing_method_eligible_for_observations_upload(case.internal_id)
        )
        is_sample_type_eligible_for_observations_upload: bool = (
            self.is_sample_type_eligible_for_observations_upload(case)
        )
        is_sample_source_eligible_for_observations_upload: bool = (
            self.is_sample_source_eligible_for_observations_upload(case.internal_id)
        )
        return (
            is_customer_eligible_for_observations_upload
            and is_sequencing_method_eligible_for_observations_upload
            and is_sample_type_eligible_for_observations_upload
            and is_sample_source_eligible_for_observations_upload
        )

    def get_loqusdb_instance(self) -> LoqusdbInstance:
        """Return the Loqusdb instance associated to the sequencing method."""
        loqusdb_instances: dict[SequencingMethod, LoqusdbInstance] = {
            SequencingMethod.WGS: LoqusdbInstance.WGS,
            SequencingMethod.WES: LoqusdbInstance.WES,
        }
        return loqusdb_instances[self.sequencing_method]

    def load_observations(self, case: Case, input_files: MipDNAObservationsInputFiles) -> None:
        """Load observation counts to Loqusdb for a MIP-DNA case."""
        if case.tumour_samples:
            LOG.error(f"Case {case.internal_id} has tumour samples. Cancelling upload.")
            raise LoqusdbUploadCaseError

        if self.is_duplicate(
            case=case,
            loqusdb_api=self.loqusdb_api,
            profile_vcf_path=input_files.profile_vcf_path,
            profile_threshold=MipDNALoadParameters.PROFILE_THRESHOLD.value,
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
            gq_threshold=MipDNALoadParameters.GQ_THRESHOLD.value,
            hard_threshold=MipDNALoadParameters.HARD_THRESHOLD.value,
            soft_threshold=MipDNALoadParameters.SOFT_THRESHOLD.value,
        )
        loqusdb_id: str = str(self.loqusdb_api.get_case(case_id=case.internal_id)[LOQUSDB_ID])
        self.update_statusdb_loqusdb_id(samples=case.samples, loqusdb_id=loqusdb_id)
        LOG.info(f"Uploaded {load_output['variants']} variants to {repr(self.loqusdb_api)}")

    def extract_observations_files_from_hk(
        self, hk_version: Version
    ) -> MipDNAObservationsInputFiles:
        """Extract observations files given a housekeeper version for rare diseases."""
        input_files: dict[str, File] = {
            "snv_vcf_path": self.housekeeper_api.files(
                version=hk_version.id, tags=[MipDNAObservationsAnalysisTag.SNV_VCF]
            ).first(),
            "sv_vcf_path": (
                self.housekeeper_api.files(
                    version=hk_version.id, tags=[MipDNAObservationsAnalysisTag.SV_VCF]
                ).first()
                if self.sequencing_method == SequencingMethod.WGS
                else None
            ),
            "profile_vcf_path": self.housekeeper_api.files(
                version=hk_version.id, tags=[MipDNAObservationsAnalysisTag.PROFILE_GBCF]
            ).first(),
            "family_ped_path": self.housekeeper_api.files(
                version=hk_version.id, tags=[MipDNAObservationsAnalysisTag.FAMILY_PED]
            ).first(),
        }
        return MipDNAObservationsInputFiles(**get_full_path_dictionary(input_files))

    def delete_case(self, case: Case) -> None:
        """Delete rare disease case observations from Loqusdb."""
        if not self.loqusdb_api.get_case(case.internal_id):
            LOG.error(
                f"Case {case.internal_id} could not be found in Loqusdb. Skipping case deletion."
            )
            raise CaseNotFoundError

        self.loqusdb_api.delete_case(case.internal_id)
        self.update_statusdb_loqusdb_id(samples=case.samples, loqusdb_id=None)
        LOG.info(f"Removed observations for case {case.internal_id} from {repr(self.loqusdb_api)}")
