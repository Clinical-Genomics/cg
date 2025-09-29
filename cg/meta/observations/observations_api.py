"""Observations API."""

import logging
from pathlib import Path

from housekeeper.store.models import Version

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.loqus import LoqusdbAPI
from cg.constants.constants import CustomerId
from cg.constants.observations import LoqusdbInstance
from cg.constants.sample_sources import SourceType
from cg.constants.sequencing import SeqLibraryPrepCategory
from cg.exc import AnalysisNotCompletedError, LoqusdbUploadCaseError
from cg.meta.workflow.analysis import AnalysisAPI
from cg.models.cg_config import CGConfig, CommonAppConfig
from cg.models.observations.input_files import (
    BalsamicObservationsInputFiles,
    MipDNAObservationsInputFiles,
    NalloObservationsInputFiles,
    RarediseaseObservationsInputFiles,
)
from cg.store.models import Analysis, Case, Sample
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class ObservationsAPI:
    """API to manage Loqusdb observations."""

    def __init__(self, config: CGConfig, analysis_api: AnalysisAPI):
        self.store: Store = config.status_db
        self.housekeeper_api: HousekeeperAPI = config.housekeeper_api
        self.analysis_api: AnalysisAPI = analysis_api
        self.loqusdb_config: CommonAppConfig = config.loqusdb
        self.loqusdb_rd_lwp_config: CommonAppConfig = config.loqusdb_rd_lwp
        self.loqusdb_wes_config: CommonAppConfig = config.loqusdb_wes
        self.loqusdb_somatic_config: CommonAppConfig = config.loqusdb_somatic
        self.loqusdb_tumor_config: CommonAppConfig = config.loqusdb_tumor
        self.loqusdb_somatic_lymphoid_config: CommonAppConfig = config.loqusdb_somatic_lymphoid
        self.loqusdb_somatic_myeloid_config: CommonAppConfig = config.loqusdb_somatic_myeloid
        self.loqusdb_somatic_exome_config: CommonAppConfig = config.loqusdb_somatic_exome

    def upload(self, case_id: str) -> None:
        """
        Upload observations to Loqusdb.

        Raises:
            LoqusdbUploadCaseError: If case is not eligible for Loqusdb uploads
        """
        case: Case = self.store.get_case_by_internal_id(internal_id=case_id)
        if self.is_case_eligible_for_observations_upload(case):
            self.load_observations(case=case)
        else:
            LOG.error(f"Case {case.internal_id} is not eligible for observations upload")
            raise LoqusdbUploadCaseError

    def get_observations_input_files(
        self, case: Case
    ) -> (
        BalsamicObservationsInputFiles
        | MipDNAObservationsInputFiles
        | NalloObservationsInputFiles
        | RarediseaseObservationsInputFiles
    ):
        """Return input files from a case to upload to Loqusdb."""
        analysis: Analysis | None = case.latest_completed_analysis
        if not analysis:
            raise AnalysisNotCompletedError(f"Case {case.internal_id} has no completed analyses")
        hk_version: Version = self.housekeeper_api.get_version_by_id(
            analysis.housekeeper_version_id
        )
        return self.get_observations_files_from_hk(hk_version=hk_version, case_id=case.internal_id)

    def get_loqusdb_api(self, loqusdb_instance: LoqusdbInstance) -> LoqusdbAPI:
        """Returns a Loqusdb API for the given Loqusdb instance."""
        loqusdb_config_map: dict = {
            LoqusdbInstance.LWP: self.loqusdb_rd_lwp_config,
            LoqusdbInstance.WGS: self.loqusdb_config,
            LoqusdbInstance.WES: self.loqusdb_wes_config,
            LoqusdbInstance.SOMATIC: self.loqusdb_somatic_config,
            LoqusdbInstance.TUMOR: self.loqusdb_tumor_config,
            LoqusdbInstance.SOMATIC_LYMPHOID: self.loqusdb_somatic_lymphoid_config,
            LoqusdbInstance.SOMATIC_MYELOID: self.loqusdb_somatic_myeloid_config,
            LoqusdbInstance.SOMATIC_EXOME: self.loqusdb_somatic_exome_config,
        }
        loqusdb_config = loqusdb_config_map[loqusdb_instance]
        return LoqusdbAPI(
            binary_path=loqusdb_config.binary_path,
            config_path=loqusdb_config.config_path,
        )

    @staticmethod
    def is_duplicate(
        case: Case,
        loqusdb_api: LoqusdbAPI,
        profile_vcf_path: Path | None = None,
        profile_threshold: float | None = None,
    ) -> bool:
        """Check if a case has already been uploaded to Loqusdb."""
        loqusdb_case: dict = loqusdb_api.get_case(case_id=case.internal_id)
        duplicate = (
            loqusdb_api.get_duplicate(
                profile_vcf_path=profile_vcf_path, profile_threshold=profile_threshold
            )
            if profile_vcf_path and profile_threshold
            else None
        )
        return bool(loqusdb_case or duplicate or case.loqusdb_uploaded_samples)

    def update_statusdb_loqusdb_id(self, samples: list[Sample], loqusdb_id: str | None) -> None:
        """Update Loqusdb ID field in StatusDB for each of the provided samples."""
        for sample in samples:
            sample.loqusdb_id = loqusdb_id
        self.store.commit_to_store()

    def is_customer_eligible_for_observations_upload(self, customer_id: str) -> bool:
        """Return whether the customer has been whitelisted for uploading observations."""
        if customer_id not in self.loqusdb_customers:
            LOG.error(f"Customer {customer_id} is not whitelisted for Loqusdb uploads")
            return False
        return True

    def is_sequencing_method_eligible_for_observations_upload(self, case_id: str) -> bool:
        """Return whether a sequencing method is valid for observations upload."""
        sequencing_method: SeqLibraryPrepCategory | None = self.analysis_api.get_data_analysis_type(
            case_id
        )
        if sequencing_method not in self.loqusdb_sequencing_methods:
            LOG.error(f"Sequencing method {sequencing_method} is not supported by Loqusdb uploads")
            return False
        return True

    def is_sample_source_type_ffpe(self, case_id: str) -> bool:
        source_type: str | None = self.analysis_api.get_case_source_type(case_id)
        if source_type and SourceType.FFPE.lower() not in source_type.lower():
            return True
        LOG.error(f"Source type {source_type} is not supported for Loqusdb uploads")
        return False

    @property
    def loqusdb_customers(self) -> list[CustomerId]:
        """Customers that are eligible for Loqusdb uploads."""
        raise NotImplementedError

    @property
    def loqusdb_sequencing_methods(self) -> list[str]:
        """Sequencing methods that are eligible for Loqusdb uploads."""
        raise NotImplementedError

    def load_observations(self, case: Case) -> None:
        """Load observation counts to Loqusdb."""
        raise NotImplementedError

    def is_case_eligible_for_observations_upload(self, case: Case) -> bool:
        """Return whether a case is eligible for observations upload."""
        raise NotImplementedError

    def get_observations_files_from_hk(
        self, hk_version: Version, case_id: str
    ) -> MipDNAObservationsInputFiles | BalsamicObservationsInputFiles:
        """Return observations files given a Housekeeper version."""
        raise NotImplementedError

    def delete_case(self, case: Case) -> None:
        """Delete case observations from Loqusdb."""
        raise NotImplementedError
