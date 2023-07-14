"""API for uploading rare disease observations."""

import logging
from typing import Dict

from housekeeper.store.models import Version, File

from cg.apps.loqus import LoqusdbAPI
from cg.constants.observations import (
    MipDNAObservationsAnalysisTag,
    MipDNALoadParameters,
    LoqusdbInstance,
    LOQUSDB_MIP_SEQUENCING_METHODS,
    LOQUSDB_ID,
    LoqusdbMipCustomers,
)
from cg.constants.sequencing import SequencingMethod
from cg.exc import LoqusdbUploadCaseError, LoqusdbDuplicateRecordError, CaseNotFoundError
from cg.meta.observations.observations_api import ObservationsAPI
from cg.models.cg_config import CGConfig
from cg.models.observations.input_files import MipDNAObservationsInputFiles
from cg.store.models import Family
from cg.utils.dict import get_full_path_dictionary

LOG = logging.getLogger(__name__)


class MipDNAObservationsAPI(ObservationsAPI):
    """API to manage MIP-DNA observations."""

    def __init__(self, config: CGConfig, sequencing_method: SequencingMethod):
        super().__init__(config)
        self.sequencing_method: SequencingMethod = sequencing_method
        self.loqusdb_api: LoqusdbAPI = self.get_loqusdb_api(self.get_loqusdb_instance())

    def get_loqusdb_instance(self) -> LoqusdbInstance:
        """Return the Loqusdb instance associated to the sequencing method."""
        if self.sequencing_method not in LOQUSDB_MIP_SEQUENCING_METHODS:
            LOG.error(
                f"Sequencing method {self.sequencing_method} is not supported by Loqusdb. Cancelling upload."
            )
            raise LoqusdbUploadCaseError

        loqusdb_instances: Dict[SequencingMethod, LoqusdbInstance] = {
            SequencingMethod.WGS: LoqusdbInstance.WGS,
            SequencingMethod.WES: LoqusdbInstance.WES,
        }
        return loqusdb_instances[self.sequencing_method]

    def load_observations(self, case: Family, input_files: MipDNAObservationsInputFiles) -> None:
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
        input_files: Dict[str, File] = {
            "snv_vcf_path": self.housekeeper_api.files(
                version=hk_version.id, tags=[MipDNAObservationsAnalysisTag.SNV_VCF]
            ).first(),
            "sv_vcf_path": self.housekeeper_api.files(
                version=hk_version.id, tags=[MipDNAObservationsAnalysisTag.SV_VCF]
            ).first()
            if self.sequencing_method == SequencingMethod.WGS
            else None,
            "profile_vcf_path": self.housekeeper_api.files(
                version=hk_version.id, tags=[MipDNAObservationsAnalysisTag.PROFILE_GBCF]
            ).first(),
            "family_ped_path": self.housekeeper_api.files(
                version=hk_version.id, tags=[MipDNAObservationsAnalysisTag.FAMILY_PED]
            ).first(),
        }
        return MipDNAObservationsInputFiles(**get_full_path_dictionary(input_files))

    def delete_case(self, case: Family) -> None:
        """Delete rare disease case observations from Loqusdb."""
        if not self.loqusdb_api.get_case(case.internal_id):
            LOG.error(
                f"Case {case.internal_id} could not be found in Loqusdb. Skipping case deletion."
            )
            raise CaseNotFoundError

        self.loqusdb_api.delete_case(case.internal_id)
        self.update_statusdb_loqusdb_id(samples=case.samples, loqusdb_id=None)
        LOG.info(f"Removed observations for case {case.internal_id} from {repr(self.loqusdb_api)}")

    def get_loqusdb_customers(self) -> LoqusdbMipCustomers:
        """Returns the customers that are entitled to Rare Disease Loqusdb uploads."""
        return LoqusdbMipCustomers
