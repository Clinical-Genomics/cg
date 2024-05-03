"""API for uploading rare disease observations."""

import logging

from housekeeper.store.models import File, Version

from cg.apps.loqus import LoqusdbAPI
from cg.constants.observations import CustomerId
from cg.constants.observations import (
    LOQUSDB_ID,
    LOQUSDB_RARE_DISEASE_CUSTOMERS,
    LoqusdbInstance,
    RarediseaseLoadParameters,
    RarediseaseObservationsAnalysisTag,
)
from cg.constants.sequencing import SequencingMethod
from cg.exc import (
    CaseNotFoundError,
    LoqusdbDuplicateRecordError,
    LoqusdbUploadCaseError,
)
from cg.meta.observations.observations_api import ObservationsAPI
from cg.models.cg_config import CGConfig
from cg.models.observations.input_files import RarediseaseObservationsInputFiles
from cg.store.models import Case
from cg.utils.dict import get_full_path_dictionary

LOG = logging.getLogger(__name__)


class RarediseaseObservationsAPI(ObservationsAPI):
    """API to manage MIP-DNA observations."""

    def __init__(self, config: CGConfig, sequencing_method: SequencingMethod):
        super().__init__(config)
        self.sequencing_method: SequencingMethod = sequencing_method
        self.loqusdb_api: LoqusdbAPI = self.get_loqusdb_api(self.set_loqusdb_instance())

    def set_loqusdb_instance(self, case_id: str) -> None:
        """Return the Loqusdb instance associated to the sequencing method."""
        sequencing_method: SequencingMethod = self.analysis_api.get_data_analysis_type(case_id)
        loqusdb_instances: dict[SequencingMethod, LoqusdbInstance] = {
            SequencingMethod.WGS: LoqusdbInstance.WGS,
            SequencingMethod.WES: LoqusdbInstance.WES,
        }
        self.loqusdb_api = self.get_loqusdb_api(loqusdb_instances[sequencing_method])

    def load_observations(self, case: Case, input_files: RarediseaseObservationsInputFiles) -> None:
        """Load observation counts to Loqusdb for a raredisease case."""
        if case.tumour_samples:
            LOG.error(f"Case {case.internal_id} has tumour samples. Cancelling upload.")
            raise LoqusdbUploadCaseError

        if self.is_duplicate(
            case=case,
            loqusdb_api=self.loqusdb_api,
            profile_vcf_path=input_files.profile_vcf_path,
            profile_threshold=RarediseaseLoadParameters.PROFILE_THRESHOLD.value,
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
            gq_threshold=RarediseaseLoadParameters.GQ_THRESHOLD.value,
            hard_threshold=RarediseaseLoadParameters.HARD_THRESHOLD.value,
            soft_threshold=RarediseaseLoadParameters.SOFT_THRESHOLD.value,
        )
        loqusdb_id: str = str(self.loqusdb_api.get_case(case_id=case.internal_id)[LOQUSDB_ID])
        self.update_statusdb_loqusdb_id(samples=case.samples, loqusdb_id=loqusdb_id)
        LOG.info(f"Uploaded {load_output['variants']} variants to {repr(self.loqusdb_api)}")

    def extract_observations_files_from_hk(
        self, hk_version: Version
    ) -> RarediseaseObservationsInputFiles:
        """Extract observations files given a housekeeper version for rare diseases."""
        input_files: dict[str, File] = {
            "snv_vcf_path": self.housekeeper_api.files(
                version=hk_version.id, tags=[RarediseaseObservationsAnalysisTag.SNV_VCF]
            ).first(),
            "sv_vcf_path": (
                self.housekeeper_api.files(
                    version=hk_version.id, tags=[RarediseaseObservationsAnalysisTag.SV_VCF]
                ).first()
                if self.sequencing_method == SequencingMethod.WGS
                else None
            ),
            "profile_vcf_path": self.housekeeper_api.files(
                version=hk_version.id, tags=[RarediseaseObservationsAnalysisTag.PROFILE_GBCF]
            ).first(),
            "family_ped_path": self.housekeeper_api.files(
                version=hk_version.id, tags=[RarediseaseObservationsAnalysisTag.FAMILY_PED]
            ).first(),
        }
        return RarediseaseObservationsInputFiles(**get_full_path_dictionary(input_files))

    def delete_case(self, case: Case) -> None:
        """Delete raredisease case observations from Loqusdb."""
        if not self.loqusdb_api.get_case(case.internal_id):
            LOG.error(
                f"Case {case.internal_id} could not be found in Loqusdb. Skipping case deletion."
            )
            raise CaseNotFoundError

        self.loqusdb_api.delete_case(case.internal_id)
        self.update_statusdb_loqusdb_id(samples=case.samples, loqusdb_id=None)
        LOG.info(f"Removed observations for case {case.internal_id} from {repr(self.loqusdb_api)}")

    @property
    def loqusdb_customers(self) -> list[CustomerId]:
        """Customers that are eligible for rare disease Loqusdb uploads."""
        return LOQUSDB_RARE_DISEASE_CUSTOMERS
