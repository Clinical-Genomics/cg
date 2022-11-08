"""API for uploading rare disease observations."""

import logging
from pathlib import Path
from typing import Dict

from housekeeper.store.models import Version, File

from cg.apps.loqus import LoqusdbAPI
from cg.constants.observations import (
    MipDNAObservationsAnalysisTag,
    MipDNALoadParameters,
    LoqusdbInstance,
    LOQUSDB_MIP_SEQUENCING_METHODS,
)
from cg.constants.sequencing import SequencingMethod
from cg.exc import LoqusdbUploadCaseError, LoqusdbDuplicateRecordError, CaseNotFoundError
from cg.meta.observations.observations_api import ObservationsAPI
from cg.models.cg_config import CGConfig
from cg.models.observations.input_files import MipDNAObservationsInputFiles
from cg.store import models

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

    def load_observations(
        self, case: models.Family, input_files: MipDNAObservationsInputFiles
    ) -> None:
        """Load observation counts to Loqusdb for a MIP-DNA case."""
        if case.tumour_samples:
            LOG.error(f"Case {case.internal_id} has tumour samples. Cancelling upload.")
            raise LoqusdbUploadCaseError

        if self.is_duplicate(case=case, profile_vcf_path=input_files.profile_vcf_path):
            LOG.error(
                f"Case {case.internal_id} has been already uploaded to {repr(self.loqusdb_api)}"
            )
            raise LoqusdbDuplicateRecordError

        output = self.loqusdb_api.load(
            case_id=case.internal_id,
            snv_vcf_path=input_files.snv_vcf_path,
            sv_vcf_path=input_files.sv_vcf_path,
            profile_vcf_path=input_files.profile_vcf_path,
            family_ped_path=input_files.family_ped_path,
            gq_threshold=MipDNALoadParameters.GQ_THRESHOLD.value,
            hard_threshold=MipDNALoadParameters.HARD_THRESHOLD.value,
            soft_threshold=MipDNALoadParameters.SOFT_THRESHOLD.value,
        )
        loqusdb_id: str = str(self.loqusdb_api.get_case(case_id=case.internal_id)["_id"])
        self.update_statusdb_loqusdb_id(samples=case.samples, loqusdb_id=loqusdb_id)
        LOG.info(f"Uploaded {output['variants']} variants to {repr(self.loqusdb_api)}")

    def is_duplicate(self, case: models.Family, profile_vcf_path: Path) -> bool:
        """Check if a case has already been uploaded to Loqusdb."""
        loqusdb_case: dict = self.loqusdb_api.get_case(case_id=case.internal_id)
        duplicate = self.loqusdb_api.get_duplicate(
            profile_vcf_path=profile_vcf_path,
            profile_threshold=MipDNALoadParameters.PROFILE_THRESHOLD.value,
        )
        return bool(loqusdb_case or duplicate or case.loqusdb_uploaded_samples)

    def extract_observations_files_from_hk(
        self, hk_version: Version
    ) -> MipDNAObservationsInputFiles:
        """Extract observations files given a housekeeper version for rare diseases."""
        snv_vcf_file: File = self.housekeeper_api.files(
            version=hk_version.id, tags=[MipDNAObservationsAnalysisTag.SNV_VCF]
        ).first()
        sv_vcf_file: File = self.housekeeper_api.files(
            version=hk_version.id, tags=[MipDNAObservationsAnalysisTag.SV_VCF]
        ).first()
        profile_vcf_file: File = self.housekeeper_api.files(
            version=hk_version.id, tags=[MipDNAObservationsAnalysisTag.PROFILE_GBCF]
        ).first()
        family_ped_path: File = self.housekeeper_api.files(
            version=hk_version.id, tags=[MipDNAObservationsAnalysisTag.FAMILY_PED]
        ).first()

        return MipDNAObservationsInputFiles(
            snv_vcf_path=snv_vcf_file.full_path if snv_vcf_file else None,
            sv_vcf_path=sv_vcf_file.full_path
            if sv_vcf_file and self.sequencing_method == SequencingMethod.WGS
            else None,
            profile_vcf_path=profile_vcf_file.full_path if profile_vcf_file else None,
            family_ped_path=family_ped_path.full_path if family_ped_path else None,
        )

    def delete_case(self, case: models.Family) -> None:
        """Delete rare disease case observations from Loqusdb."""
        if not self.loqusdb_api.get_case(case.internal_id):
            LOG.error(
                f"Case {case.internal_id} could not be found in Loqusdb. Skipping case deletion."
            )
            raise CaseNotFoundError

        self.loqusdb_api.delete_case(case.internal_id)
        self.update_statusdb_loqusdb_id(samples=case.samples, loqusdb_id=None)
        LOG.info(f"Removed observations for case {case.internal_id} from {repr(self.loqusdb_api)}")
