"""API for uploading cancer observations."""

import logging
from typing import Dict, List

from cg.apps.loqus import LoqusdbAPI
from cg.constants.observations import (
    BalsamicObservationsAnalysisTag,
    LoqusdbInstance,
    LOQUSDB_BALSAMIC_SEQUENCING_METHODS,
    BalsamicLoadParameters,
    LOQUSDB_ID,
    LoqusdbBalsamicCustomers,
)
from cg.exc import LoqusdbUploadCaseError, CaseNotFoundError, LoqusdbDuplicateRecordError
from cg.store.models import Family

from housekeeper.store.models import Version, File

from cg.constants.sequencing import SequencingMethod
from cg.meta.observations.observations_api import ObservationsAPI
from cg.models.cg_config import CGConfig
from cg.models.observations.input_files import BalsamicObservationsInputFiles
from cg.utils.dict import get_full_path_dictionary

LOG = logging.getLogger(__name__)


class BalsamicObservationsAPI(ObservationsAPI):
    """API to manage Balsamic observations."""

    def __init__(self, config: CGConfig, sequencing_method: SequencingMethod):
        super().__init__(config)
        self.sequencing_method: SequencingMethod = sequencing_method
        self.loqusdb_somatic_api: LoqusdbAPI = self.get_loqusdb_api(LoqusdbInstance.SOMATIC)
        self.loqusdb_tumor_api: LoqusdbAPI = self.get_loqusdb_api(LoqusdbInstance.TUMOR)

    def load_observations(self, case: Family, input_files: BalsamicObservationsInputFiles) -> None:
        """Load observation counts to Loqusdb for a Balsamic case."""
        if self.sequencing_method not in LOQUSDB_BALSAMIC_SEQUENCING_METHODS:
            LOG.error(
                f"Sequencing method {self.sequencing_method} is not supported by Loqusdb. Cancelling upload."
            )
            raise LoqusdbUploadCaseError

        loqusdb_upload_apis: List[LoqusdbAPI] = [self.loqusdb_somatic_api, self.loqusdb_tumor_api]
        for loqusdb_api in loqusdb_upload_apis:
            if self.is_duplicate(
                case=case,
                loqusdb_api=loqusdb_api,
                profile_vcf_path=None,
                profile_threshold=None,
            ):
                LOG.error(f"Case {case.internal_id} has already been uploaded to Loqusdb")
                raise LoqusdbDuplicateRecordError

        for loqusdb_api in loqusdb_upload_apis:
            self.load_cancer_observations(
                case=case, input_files=input_files, loqusdb_api=loqusdb_api
            )

        # Update Statusb with a germline Loqusdb ID
        loqusdb_id: str = str(self.loqusdb_tumor_api.get_case(case_id=case.internal_id)[LOQUSDB_ID])
        self.update_statusdb_loqusdb_id(samples=case.samples, loqusdb_id=loqusdb_id)

    @staticmethod
    def load_cancer_observations(
        case: Family,
        input_files: BalsamicObservationsInputFiles,
        loqusdb_api: LoqusdbAPI,
    ) -> None:
        """Load cancer observations to a specific Loqusdb API."""
        is_somatic: bool = "somatic" in str(loqusdb_api.config_path)
        load_output: dict = loqusdb_api.load(
            case_id=case.internal_id,
            snv_vcf_path=input_files.snv_vcf_path if is_somatic else input_files.snv_all_vcf_path,
            sv_vcf_path=input_files.sv_vcf_path if is_somatic else None,
            profile_vcf_path=None,
            gq_threshold=BalsamicLoadParameters.GQ_THRESHOLD.value,
            hard_threshold=BalsamicLoadParameters.HARD_THRESHOLD.value,
            soft_threshold=BalsamicLoadParameters.SOFT_THRESHOLD.value,
        )
        LOG.info(f"Uploaded {load_output['variants']} variants to {repr(loqusdb_api)}")

    def extract_observations_files_from_hk(
        self, hk_version: Version
    ) -> BalsamicObservationsInputFiles:
        """Extract observations files given a housekeeper version for cancer."""
        input_files: Dict[str, File] = {
            "snv_vcf_path": self.housekeeper_api.files(
                version=hk_version.id, tags=[BalsamicObservationsAnalysisTag.SNV_VCF]
            ).first(),
            "snv_all_vcf_path": self.housekeeper_api.files(
                version=hk_version.id, tags=[BalsamicObservationsAnalysisTag.SNV_ALL_VCF]
            ).first(),
            "sv_vcf_path": self.housekeeper_api.files(
                version=hk_version.id, tags=[BalsamicObservationsAnalysisTag.SV_VCF]
            ).first(),
            "profile_vcf_path": None,
        }
        return BalsamicObservationsInputFiles(**get_full_path_dictionary(input_files))

    def delete_case(self, case: Family) -> None:
        """Delete cancer case observations from Loqusdb."""
        loqusdb_apis: List[LoqusdbAPI] = [self.loqusdb_somatic_api, self.loqusdb_tumor_api]
        for loqusdb_api in loqusdb_apis:
            if not loqusdb_api.get_case(case.internal_id):
                LOG.error(
                    f"Case {case.internal_id} could not be found in Loqusdb. Skipping case deletion."
                )
                raise CaseNotFoundError

        for loqusdb_api in loqusdb_apis:
            loqusdb_api.delete_case(case.internal_id)
        self.update_statusdb_loqusdb_id(samples=case.samples, loqusdb_id=None)
        LOG.info(f"Removed observations for case {case.internal_id} from Loqusdb")

    def get_loqusdb_customers(self) -> LoqusdbBalsamicCustomers:
        """Returns the customers that are entitled to Cancer Loqusdb uploads."""
        return LoqusdbBalsamicCustomers
