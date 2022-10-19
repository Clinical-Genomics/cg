"""API for uploading rare disease observations."""

import logging
from pathlib import Path
from typing import List

from housekeeper.store.models import Version, File

from cg.apps.loqus import LoqusdbAPI
from cg.constants.observations import MipDNAObservationsAnalysisTag, MipDNALoadParameters
from cg.constants.sequencing import SequencingMethod
from cg.exc import DataIntegrityError
from cg.meta.upload.observations.observations_api import ObservationsAPI
from cg.models.cg_config import CGConfig
from cg.models.observations.input_files import MipDNAObservationsInputFiles
from cg.store import models

LOG = logging.getLogger(__name__)


class MipDNAObservationsAPI(ObservationsAPI):
    """API to manage MIP-DNA observations."""

    def __init__(self, config: CGConfig, sequencing_method: SequencingMethod):
        super().__init__(config, sequencing_method)

    def load_observations(
        self,
        case: models.Family,
        loqusdb_api: LoqusdbAPI,
        input_files: MipDNAObservationsInputFiles,
    ) -> None:
        """Load an observations count to Loqusdb for a MIP-DNA case."""

        output = loqusdb_api.load(
            case_id=case.internal_id,
            snv_vcf_path=input_files.snv_vcf_path,
            sv_vcf_path=input_files.sv_vcf_path,
            profile_vcf_path=input_files.profile_vcf_path,
            family_ped_path=input_files.family_ped_path,
            gq_threshold=MipDNALoadParameters.GQ_THRESHOLD.value,
            hard_threshold=MipDNALoadParameters.HARD_THRESHOLD.value,
            soft_threshold=MipDNALoadParameters.SOFT_THRESHOLD.value,
        )
        loqusdb_id = str(loqusdb_api.get_case(case.internal_id)["_id"])
        self.update_loqusdb_id(case.get_samples_in_case, loqusdb_id)
        LOG.info(f"Uploaded {output['variants']} variants to {Path(loqusdb_api.config_path).stem}")

    def get_loqusdb_api(self, case: models.Family) -> LoqusdbAPI:
        """Return a Loqusdb API specific to the analysis type."""
        if case.get_tumour_samples:
            LOG.error(f"Case {case.internal_id} has tumour samples. Cancelling its upload.")
            raise DataIntegrityError

        binary_path, config_path = (
            (self.loqusdb.binary_path, self.loqusdb.config_path)
            if self.sequencing_method == SequencingMethod.WGS
            else (self.loqusdb_wes.binary_path, self.loqusdb_wes.config_path)
        )

        return LoqusdbAPI(binary_path=binary_path, config_path=config_path)

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
            snv_vcf_path=snv_vcf_file.full_path,
            sv_vcf_path=sv_vcf_file.full_path
            if self.sequencing_method == SequencingMethod.WGS
            else None,
            profile_vcf_path=profile_vcf_file.full_path,
            family_ped_path=family_ped_path.full_path,
        )

    def is_duplicate(
        self,
        case: models.Family,
        loqusdb_api: LoqusdbAPI,
        input_files: MipDNAObservationsInputFiles,
    ) -> bool:
        """Check if a case has been already uploaded to Loqusdb."""
        loqusdb_case: dict = loqusdb_api.get_case(case.internal_id)
        duplicate = loqusdb_api.get_duplicate(
            input_files.profile_vcf_path, MipDNALoadParameters.PROFILE_THRESHOLD.value
        )
        if loqusdb_case or duplicate or case.get_loqusdb_uploaded_samples:
            return True
        return False

    def get_supported_sequencing_methods(self) -> List[SequencingMethod]:
        """Return a list of supported sequencing methods for Loqusdb upload."""
        return [SequencingMethod.WGS, SequencingMethod.WES]
