"""Observations API."""

import logging
from datetime import datetime
from typing import List, Optional

from housekeeper.store.models import Version

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.loqus import LoqusdbAPI
from cg.constants.sequencing import SequencingMethod
from cg.exc import LoqusdbUploadCaseError, LoqusdbDuplicateRecordError
from cg.models.cg_config import CGConfig, CommonAppConfig
from cg.models.observations.input_files import ObservationsInputFiles
from cg.store import Store, models

LOG = logging.getLogger(__name__)


class ObservationsAPI:
    """API to manage Loqusdb observations."""

    def __init__(self, config: CGConfig, sequencing_method: SequencingMethod):
        self.store: Store = config.status_db
        self.housekeeper_api: HousekeeperAPI = config.housekeeper_api
        self.sequencing_method: SequencingMethod = sequencing_method

    def upload(self, case: models.Family) -> None:
        """Upload observations to Loqusdb."""
        if self.sequencing_method not in self.get_supported_sequencing_methods():
            LOG.error(
                f"Sequencing method {self.sequencing_method} is not supported by Loqusdb. Cancelling its upload"
            )
            raise LoqusdbUploadCaseError

        loqusdb_api: LoqusdbAPI = self.get_loqusdb_api(case)
        input_files: ObservationsInputFiles = self.get_observations_input_files(case)
        if self.is_duplicate(case, loqusdb_api, input_files):
            LOG.error(f"Case {case.internal_id} has been already uploaded to {repr(loqusdb_api)}")
            raise LoqusdbDuplicateRecordError

        self.load_observations(case, loqusdb_api, input_files)
        LOG.info(f"Observations uploaded for case {case.internal_id} to {repr(loqusdb_api)}")

    def get_observations_input_files(self, case: models.Family) -> ObservationsInputFiles:
        """Fetch input files from a case to upload to Loqusdb."""
        analysis: models.Analysis = case.analyses[0]
        analysis_date: datetime = analysis.started_at or analysis.completed_at
        hk_version: Version = self.housekeeper_api.version(
            analysis.family.internal_id, analysis_date
        )
        return self.extract_observations_files_from_hk(hk_version)

    def update_loqusdb_id(self, samples: List[models.Family], loqusdb_id: Optional[str]) -> None:
        """Update Loqusdb ID field in StatusDB for each of the provided samples."""
        for sample in samples:
            sample.loqusdb_id = loqusdb_id
        self.store.commit()

    def load_observations(
        self, case: models.Family, loqusdb_api: LoqusdbAPI, input_files: ObservationsInputFiles
    ) -> None:
        """Load an observations count to Loqusdb."""
        raise NotImplementedError

    def get_loqusdb_api(self, case: models.Family) -> LoqusdbAPI:
        """Return a Loqusdb API specific to the analysis type."""
        raise NotImplementedError

    def extract_observations_files_from_hk(self, hk_version: Version) -> ObservationsInputFiles:
        """Extract observations files given a housekeeper version."""
        raise NotImplementedError

    def is_duplicate(
        self, case: models.Family, loqusdb_api: LoqusdbAPI, input_files: ObservationsInputFiles
    ) -> bool:
        """Check if a case has been already uploaded to Loqusdb."""
        raise NotImplementedError

    def get_supported_sequencing_methods(self) -> List[SequencingMethod]:
        """Return a list of supported sequencing methods for Loqusdb upload."""
        raise NotImplementedError

    def delete_case(self, case: models.Family) -> None:
        """Delete case observations from Loqusdb."""
        raise NotImplementedError
