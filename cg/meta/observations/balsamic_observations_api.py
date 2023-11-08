"""API for uploading cancer observations."""
import logging
from pathlib import Path

from housekeeper.store.models import File, Version

from cg.apps.loqus import LoqusdbAPI
from cg.constants.observations import (
    LOQUSDB_BALSAMIC_SEQUENCING_METHODS,
    LOQUSDB_ID,
    BalsamicLoadParameters,
    BalsamicObservationsAnalysisTag,
    LoqusdbBalsamicCustomers,
    LoqusdbInstance,
)
from cg.constants.sequencing import SequencingMethod
from cg.exc import (
    CaseNotFoundError,
    LoqusdbDuplicateRecordError,
    LoqusdbUploadCaseError,
)
from cg.meta.observations.observations_api import ObservationsAPI
from cg.models.cg_config import CGConfig
from cg.models.observations.input_files import BalsamicObservationsInputFiles
from cg.store.models import Case
from cg.utils.dict import get_full_path_dictionary

LOG = logging.getLogger(__name__)


class BalsamicObservationsAPI(ObservationsAPI):
    """API to manage Balsamic observations."""

    def __init__(self, config: CGConfig, sequencing_method: SequencingMethod):
        super().__init__(config)
        self.sequencing_method: SequencingMethod = sequencing_method
        self.loqusdb_somatic_api: LoqusdbAPI = self.get_loqusdb_api(LoqusdbInstance.SOMATIC)
        self.loqusdb_tumor_api: LoqusdbAPI = self.get_loqusdb_api(LoqusdbInstance.TUMOR)

    def load_observations(self, case: Case, input_files: BalsamicObservationsInputFiles) -> None:
        """Load observation counts to Loqusdb for a Balsamic case."""
        if self.sequencing_method not in LOQUSDB_BALSAMIC_SEQUENCING_METHODS:
            LOG.error(
                f"Sequencing method {self.sequencing_method} is not supported by Loqusdb. Cancelling upload."
            )
            raise LoqusdbUploadCaseError

        loqusdb_upload_apis: list[LoqusdbAPI] = [self.loqusdb_somatic_api, self.loqusdb_tumor_api]
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

        # Update Statusdb with a germline Loqusdb ID
        loqusdb_id: str = str(self.loqusdb_tumor_api.get_case(case_id=case.internal_id)[LOQUSDB_ID])
        self.update_statusdb_loqusdb_id(samples=case.samples, loqusdb_id=loqusdb_id)

    def load_cancer_observations(
        self, case: Case, input_files: BalsamicObservationsInputFiles, loqusdb_api: LoqusdbAPI
    ) -> None:
        """Load cancer observations to a specific Loqusdb API."""
        is_somatic_db: bool = "somatic" in str(loqusdb_api.config_path)
        is_paired_analysis: bool = len(self.store.get_samples_by_case_id(case.internal_id)) == 2
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
            gq_threshold=BalsamicLoadParameters.QUAL_THRESHOLD.value
            if is_somatic_db
            else BalsamicLoadParameters.QUAL_GERMLINE_THRESHOLD.value,
        )
        LOG.info(f"Uploaded {load_output['variants']} variants to {repr(loqusdb_api)}")

    def extract_observations_files_from_hk(
        self, hk_version: Version
    ) -> BalsamicObservationsInputFiles:
        """Extract observations files given a housekeeper version for cancer."""
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

    def delete_case(self, case: Case) -> None:
        """Delete cancer case observations from Loqusdb."""
        loqusdb_apis: list[LoqusdbAPI] = [self.loqusdb_somatic_api, self.loqusdb_tumor_api]
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
