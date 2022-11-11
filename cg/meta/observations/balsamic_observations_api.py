"""API for uploading cancer observations."""

import logging

from cg.apps.loqus import LoqusdbAPI
from cg.constants.observations import (
    BalsamicObservationsAnalysisTag,
    LoqusdbInstance,
    LOQUSDB_BALSAMIC_SEQUENCING_METHODS,
    BalsamicLoadParameters,
)
from cg.exc import LoqusdbUploadCaseError, CaseNotFoundError, LoqusdbDuplicateRecordError
from cg.store import models
from housekeeper.store.models import Version, File

from cg.constants.sequencing import SequencingMethod
from cg.meta.observations.observations_api import ObservationsAPI
from cg.models.cg_config import CGConfig
from cg.models.observations.input_files import BalsamicObservationsInputFiles

LOG = logging.getLogger(__name__)


class BalsamicObservationsAPI(ObservationsAPI):
    """API to manage Balsamic observations."""

    def __init__(self, config: CGConfig, sequencing_method: SequencingMethod):
        super().__init__(config)
        self.sequencing_method: SequencingMethod = sequencing_method
        self.loqusdb_somatic_api: LoqusdbAPI = self.get_loqusdb_api(LoqusdbInstance.SOMATIC)
        self.loqusdb_tumor_api: LoqusdbAPI = self.get_loqusdb_api(LoqusdbInstance.TUMOR)

    def load_observations(
        self, case: models.Family, input_files: BalsamicObservationsInputFiles
    ) -> None:
        """Load observation counts to Loqusdb for a Balsamic case."""
        if self.sequencing_method not in LOQUSDB_BALSAMIC_SEQUENCING_METHODS:
            LOG.error(
                f"Sequencing method {self.sequencing_method} is not supported by Loqusdb. Cancelling upload."
            )
            raise LoqusdbUploadCaseError

        duplicate_somatic: bool = self.is_duplicate(
            case=case,
            loqusdb_api=self.loqusdb_somatic_api,
            profile_vcf_path=input_files.profile_vcf_path,
            profile_threshold=BalsamicLoadParameters.PROFILE_THRESHOLD,
        )
        duplicate_tumor: bool = self.is_duplicate(
            case=case,
            loqusdb_api=self.loqusdb_tumor_api,
            profile_vcf_path=input_files.profile_vcf_path,
            profile_threshold=BalsamicLoadParameters.PROFILE_THRESHOLD,
        )
        if duplicate_somatic or duplicate_tumor:
            LOG.error(f"Case {case.internal_id} has already been uploaded to Loqusdb")
            raise LoqusdbDuplicateRecordError

        self.load_cancer_observations(
            case=case, input_files=input_files, loqusdb_api=self.loqusdb_somatic_api
        )
        self.load_cancer_observations(
            case=case, input_files=input_files, loqusdb_api=self.loqusdb_tumor_api
        )
        loqusdb_id: str = str(self.loqusdb_somatic_api.get_case(case_id=case.internal_id)["_id"])
        self.update_statusdb_loqusdb_id(samples=case.samples, loqusdb_id=loqusdb_id)

    @staticmethod
    def load_cancer_observations(
        case: models.Family,
        input_files: BalsamicObservationsInputFiles,
        loqusdb_api: LoqusdbAPI,
    ) -> None:
        """Load cancer observations to a specific Loqusdb API."""
        is_somatic: bool = True if "somatic" in loqusdb_api.config_path else False
        load_output: dict = loqusdb_api.load(
            case_id=case.internal_id,
            snv_vcf_path=input_files.snv_vcf_path if is_somatic else input_files.snv_all_vcf_path,
            sv_vcf_path=input_files.sv_vcf_path if is_somatic else None,
            profile_vcf_path=input_files.profile_vcf_path,
            gq_threshold=BalsamicLoadParameters.GQ_THRESHOLD.value,
            hard_threshold=BalsamicLoadParameters.HARD_THRESHOLD.value,
            soft_threshold=BalsamicLoadParameters.SOFT_THRESHOLD.value,
        )
        LOG.info(f"Uploaded {load_output['variants']} variants to {repr(loqusdb_api)}")

    def extract_observations_files_from_hk(
        self, hk_version: Version
    ) -> BalsamicObservationsInputFiles:
        """Extract observations files given a housekeeper version for cancer."""
        snv_vcf_file: File = self.housekeeper_api.files(
            version=hk_version.id, tags=[BalsamicObservationsAnalysisTag.SNV_VCF]
        ).first()
        snv_all_vcf_file: File = self.housekeeper_api.files(
            version=hk_version.id, tags=[BalsamicObservationsAnalysisTag.SNV_ALL_VCF]
        ).first()
        sv_vcf_file: File = self.housekeeper_api.files(
            version=hk_version.id, tags=[BalsamicObservationsAnalysisTag.SV_VCF]
        ).first()
        profile_vcf_file: File = self.housekeeper_api.files(
            version=hk_version.id, tags=[BalsamicObservationsAnalysisTag.PROFILE_VCF]
        ).first()

        return BalsamicObservationsInputFiles(
            snv_vcf_path=snv_vcf_file.full_path if snv_vcf_file else None,
            snv_all_vcf_path=snv_all_vcf_file.full_path if snv_all_vcf_file else None,
            sv_vcf_path=sv_vcf_file.full_path if sv_vcf_file else None,
            profile_vcf_path=profile_vcf_file.full_path if profile_vcf_file else None,
        )

    def delete_case(self, case: models.Family) -> None:
        """Delete cancer case observations from Loqusdb."""
        if not self.loqusdb_somatic_api.get_case(
            case.internal_id
        ) or not self.loqusdb_tumor_api.get_case(case.internal_id):
            LOG.error(
                f"Case {case.internal_id} could not be found in Loqusdb. Skipping case deletion."
            )
            raise CaseNotFoundError

        self.loqusdb_somatic_api.delete_case(case.internal_id)
        self.loqusdb_tumor_api.delete_case(case.internal_id)
        self.update_statusdb_loqusdb_id(samples=case.samples, loqusdb_id=None)
        LOG.info(f"Removed observations for case {case.internal_id} from Loqusdb")
