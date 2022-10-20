"""API for uploading cancer observations."""

import logging
from typing import List

from cg.store import models
from housekeeper.store.models import Version

from cg.apps.loqus import LoqusdbAPI
from cg.constants.sequencing import SequencingMethod
from cg.meta.observations.observations_api import ObservationsAPI
from cg.models.cg_config import CGConfig, CommonAppConfig
from cg.models.observations.input_files import BalsamicObservationsInputFiles

LOG = logging.getLogger(__name__)


class BalsamicObservationsAPI(ObservationsAPI):
    """API to manage Balsamic observations."""

    def __init__(self, config: CGConfig, sequencing_method: SequencingMethod):
        self.loqusdb_somatic: CommonAppConfig = config.loqusdb_somatic
        self.loqusdb_tumor: CommonAppConfig = config.loqusdb_tumor
        super().__init__(config, sequencing_method)

    def load_observations(
        self,
        case: models.Family,
        loqusdb_api: LoqusdbAPI,
        input_files: BalsamicObservationsInputFiles,
    ) -> None:
        """Load an observations count to Loqusdb for a Balsamic case."""
        raise NotImplementedError

    def get_loqusdb_api(self, case: models.Family) -> LoqusdbAPI:
        """Return a Loqusdb API specific to the analysis type."""
        raise NotImplementedError

    def extract_observations_files_from_hk(
        self, hk_version: Version
    ) -> BalsamicObservationsInputFiles:
        """Extract observations files given a housekeeper version for cancer."""
        raise NotImplementedError

    def is_duplicate(
        self,
        case: models.Family,
        loqusdb_api: LoqusdbAPI,
        input_files: BalsamicObservationsInputFiles,
    ) -> bool:
        """Check if a case has been already uploaded to Loqusdb."""
        raise NotImplementedError

    def get_supported_sequencing_methods(self) -> List[SequencingMethod]:
        """Return a list of supported sequencing methods for Loqusdb upload."""
        raise NotImplementedError

    def delete_case(self, case: models.Family) -> None:
        """Delete cancer case observations from Loqusdb."""
        raise NotImplementedError
