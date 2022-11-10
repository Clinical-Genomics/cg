"""API for uploading cancer observations."""

import logging

from cg.apps.loqus import LoqusdbAPI
from cg.constants.observations import (
    BalsamicObservationsAnalysisTag,
    LoqusdbInstance,
    LOQUSDB_BALSAMIC_SEQUENCING_METHODS,
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

        if self.is_duplicate(case=case, loqusdb_api=self.loqusdb_somatic_api) or self.is_duplicate(
            case=case, loqusdb_api=self.loqusdb_tumor_api
        ):
            LOG.error(f"Case {case.internal_id} has already been uploaded to Loqusdb")
            raise LoqusdbDuplicateRecordError

        self.load_somatic_observations(case=models.Family, input_files=input_files)
        self.load_tumor_observations(case=models.Family, input_files=input_files)

    @staticmethod
    def is_duplicate(case: models.Family, loqusdb_api: LoqusdbAPI) -> bool:
        """Check if a case has already been uploaded to Loqusdb."""
        loqusdb_case: dict = loqusdb_api.get_case(case_id=case.internal_id)
        return bool(loqusdb_case or case.loqusdb_uploaded_samples)

    def load_somatic_observations(
        self, case: models.Family, input_files: BalsamicObservationsInputFiles
    ) -> None:
        """Load cancer somatic observations."""
        load_output = self.loqusdb_somatic_api.load(
            case_id=case.internal_id,
            snv_vcf_path=input_files.snv_vcf_path,
            sv_vcf_path=input_files.sv_vcf_path,
        )
        loqusdb_id: str = str(self.loqusdb_somatic_api.get_case(case_id=case.internal_id)["_id"])
        self.update_statusdb_loqusdb_id(samples=case.samples, loqusdb_id=loqusdb_id)
        LOG.info(f"Uploaded {load_output['variants']} variants to {repr(self.loqusdb_somatic_api)}")

    def load_tumor_observations(
        self, case: models.Family, input_files: BalsamicObservationsInputFiles
    ) -> None:
        """Load cancer germline observations."""
        load_output = self.loqusdb_tumor_api.load(
            case_id=case.internal_id, snv_vcf_path=input_files.snv_all_vcf_path
        )
        loqusdb_id: str = str(self.loqusdb_tumor_api.get_case(case_id=case.internal_id)["_id"])
        self.update_statusdb_loqusdb_id(samples=case.samples, loqusdb_id=loqusdb_id)
        LOG.info(f"Uploaded {load_output['variants']} variants to {repr(self.loqusdb_tumor_api)}")

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

        return BalsamicObservationsInputFiles(
            snv_vcf_path=snv_vcf_file.full_path if snv_vcf_file else None,
            snv_all_vcf_path=snv_all_vcf_file.full_path if snv_all_vcf_file else None,
            sv_vcf_path=sv_vcf_file.full_path if sv_vcf_file else None,
        )

    def delete_case(self, case: models.Family) -> None:
        """Delete cancer case observations from Loqusdb."""
        if not self.loqusdb_somatic_api.get_case(
            case.internal_id
        ) or not self.loqusdb_tumor_api.get_case(case.internal_id):
            LOG.error(
                f"Skipping case deletion. Case {case.internal_id} could not be found in Loqusdb."
            )
            raise CaseNotFoundError

        self.loqusdb_somatic_api.delete_case(case.internal_id)
        self.loqusdb_tumor_api.delete_case(case.internal_id)
        self.update_statusdb_loqusdb_id(samples=case.samples, loqusdb_id=None)
        LOG.info(f"Removed observations for case {case.internal_id} from Loqusdb")
