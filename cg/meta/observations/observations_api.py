"""Observations API."""

import logging
from datetime import datetime
from pathlib import Path

from housekeeper.store.models import Version

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.loqus import LoqusdbAPI
from cg.constants.observations import LoqusdbInstance
from cg.exc import LoqusdbUploadCaseError
from cg.models.cg_config import CGConfig, CommonAppConfig
from cg.models.observations.input_files import (
    BalsamicObservationsInputFiles,
    MipDNAObservationsInputFiles,
)
from cg.store.models import Analysis, Case
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class ObservationsAPI:
    """API to manage Loqusdb observations."""

    def __init__(self, config: CGConfig):
        self.store: Store = config.status_db
        self.housekeeper_api: HousekeeperAPI = config.housekeeper_api
        self.loqusdb_config: CommonAppConfig = config.loqusdb
        self.loqusdb_wes_config: CommonAppConfig = config.loqusdb_wes
        self.loqusdb_somatic_config: CommonAppConfig = config.loqusdb_somatic
        self.loqusdb_tumor_config: CommonAppConfig = config.loqusdb_tumor

    def upload(self, case: Case) -> None:
        """Upload observations to Loqusdb."""
        is_case_eligible_for_loqusdb_upload: bool = self.is_case_eligible_for_observations_upload(
            case
        )
        if is_case_eligible_for_loqusdb_upload:
            input_files: MipDNAObservationsInputFiles | BalsamicObservationsInputFiles = (
                self.get_observations_input_files(case)
            )
            self.load_observations(case=case, input_files=input_files)
        else:
            LOG.error(f"Case {case.internal_id} is not eligible for observations upload")
            raise LoqusdbUploadCaseError

    def is_case_eligible_for_observations_upload(self, case: Case) -> bool:
        """Return whether a case is eligible for observations upload."""
        is_customer_eligible_for_observations_upload: bool = (
            self.is_customer_eligible_for_observations_upload(case.customer.internal_id)
        )
        return is_customer_eligible_for_observations_upload

    def is_customer_eligible_for_observations_upload(self, customer_id: str) -> bool:
        """Return whether the customer is whitelisted for uploading observations."""
        if customer_id not in self.get_loqusdb_customers():
            LOG.error(f"Customer {customer_id} is not whitelisted for Loqusdb uploads")
            return False
        return True

    def get_observations_input_files(
        self, case: Case
    ) -> MipDNAObservationsInputFiles | BalsamicObservationsInputFiles:
        """Fetch input files from a case to upload to Loqusdb."""
        analysis: Analysis = case.analyses[0]
        analysis_date: datetime = analysis.started_at or analysis.completed_at
        hk_version: Version = self.housekeeper_api.version(analysis.case.internal_id, analysis_date)
        return self.extract_observations_files_from_hk(hk_version)

    def get_loqusdb_api(self, loqusdb_instance: LoqusdbInstance) -> LoqusdbAPI:
        """Returns a Loqusdb API for the given Loqusdb instance."""
        loqusdb_apis = {
            LoqusdbInstance.WGS: LoqusdbAPI(
                binary_path=self.loqusdb_config.binary_path,
                config_path=self.loqusdb_config.config_path,
            ),
            LoqusdbInstance.WES: LoqusdbAPI(
                binary_path=self.loqusdb_wes_config.binary_path,
                config_path=self.loqusdb_wes_config.config_path,
            ),
            LoqusdbInstance.SOMATIC: LoqusdbAPI(
                binary_path=self.loqusdb_somatic_config.binary_path,
                config_path=self.loqusdb_somatic_config.config_path,
            ),
            LoqusdbInstance.TUMOR: LoqusdbAPI(
                binary_path=self.loqusdb_tumor_config.binary_path,
                config_path=self.loqusdb_tumor_config.config_path,
            ),
        }
        return loqusdb_apis[loqusdb_instance]

    @staticmethod
    def is_duplicate(
        case: Case,
        loqusdb_api: LoqusdbAPI,
        profile_vcf_path: Path | None,
        profile_threshold: float | None,
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

    def update_statusdb_loqusdb_id(self, samples: list[Case], loqusdb_id: str | None) -> None:
        """Update Loqusdb ID field in StatusDB for each of the provided samples."""
        for sample in samples:
            sample.loqusdb_id = loqusdb_id
        self.store.session.commit()

    def get_loqusdb_customers(self) -> list[str]:
        """Return customers that are eligible for Loqusdb uploads."""
        raise NotImplementedError

    def load_observations(
        self,
        case: Case,
        input_files: MipDNAObservationsInputFiles | BalsamicObservationsInputFiles,
    ) -> None:
        """Load observation counts to Loqusdb."""
        raise NotImplementedError

    def extract_observations_files_from_hk(
        self, hk_version: Version
    ) -> MipDNAObservationsInputFiles | BalsamicObservationsInputFiles:
        """Extract observations files given a housekeeper version."""
        raise NotImplementedError

    def delete_case(self, case: Case) -> None:
        """Delete case observations from Loqusdb."""
        raise NotImplementedError
