"""Observations API."""

import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Union

from housekeeper.store.models import Version

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.loqus import LoqusdbAPI
from cg.constants.observations import LoqusdbInstance, LoqusdbBalsamicCustomers, LoqusdbMipCustomers
from cg.exc import LoqusdbUploadCaseError
from cg.models.cg_config import CGConfig, CommonAppConfig
from cg.models.observations.input_files import (
    MipDNAObservationsInputFiles,
    BalsamicObservationsInputFiles,
)
from cg.store import Store
from cg.store.models import Customer, Family, Analysis

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

    def upload(self, case: Family) -> None:
        """Upload observations to Loqusdb."""
        self.check_customer_loqusdb_permissions(case.customer)
        input_files: Union[
            MipDNAObservationsInputFiles, BalsamicObservationsInputFiles
        ] = self.get_observations_input_files(case)
        self.load_observations(case=case, input_files=input_files)

    def get_observations_input_files(
        self, case: Family
    ) -> Union[MipDNAObservationsInputFiles, BalsamicObservationsInputFiles]:
        """Fetch input files from a case to upload to Loqusdb."""
        analysis: Analysis = case.analyses[0]
        analysis_date: datetime = analysis.started_at or analysis.completed_at
        hk_version: Version = self.housekeeper_api.version(
            analysis.family.internal_id, analysis_date
        )
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
        case: Family,
        loqusdb_api: LoqusdbAPI,
        profile_vcf_path: Optional[Path],
        profile_threshold: Optional[float],
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

    def update_statusdb_loqusdb_id(self, samples: List[Family], loqusdb_id: Optional[str]) -> None:
        """Update Loqusdb ID field in StatusDB for each of the provided samples."""
        for sample in samples:
            sample.loqusdb_id = loqusdb_id
        self.store.session.commit()

    def check_customer_loqusdb_permissions(self, customer: Customer) -> None:
        """Verifies that the customer is whitelisted for Loqusdb uploads."""
        if customer.internal_id not in [cust_id.value for cust_id in self.get_loqusdb_customers()]:
            LOG.error(
                f"Customer {customer.internal_id} is not whitelisted for Loqusdb uploads. Cancelling upload."
            )
            raise LoqusdbUploadCaseError
        LOG.info(f"Valid customer {customer.internal_id} for Loqusdb uploads")

    def get_loqusdb_customers(self) -> Union[LoqusdbMipCustomers, LoqusdbBalsamicCustomers]:
        """Returns the customers that are entitled to Loqusdb uploads."""
        raise NotImplementedError

    def load_observations(
        self,
        case: Family,
        input_files: Union[MipDNAObservationsInputFiles, BalsamicObservationsInputFiles],
    ) -> None:
        """Load observation counts to Loqusdb."""
        raise NotImplementedError

    def extract_observations_files_from_hk(
        self, hk_version: Version
    ) -> Union[MipDNAObservationsInputFiles, BalsamicObservationsInputFiles]:
        """Extract observations files given a housekeeper version."""
        raise NotImplementedError

    def delete_case(self, case: Family) -> None:
        """Delete case observations from Loqusdb."""
        raise NotImplementedError
