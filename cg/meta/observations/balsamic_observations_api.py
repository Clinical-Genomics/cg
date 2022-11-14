"""API for uploading cancer observations."""

import logging

from cg.store import models
from housekeeper.store.models import Version

from cg.constants.sequencing import SequencingMethod
from cg.meta.observations.observations_api import ObservationsAPI
from cg.models.cg_config import CGConfig
from cg.models.observations.input_files import BalsamicObservationsInputFiles

LOG = logging.getLogger(__name__)


class BalsamicObservationsAPI(ObservationsAPI):
    """API to manage Balsamic observations."""

    def __init__(self, config: CGConfig, sequencing_method: SequencingMethod):
        self.sequencing_method: SequencingMethod = sequencing_method
        super().__init__(config)

    def load_observations(
        self, case: models.Family, input_files: BalsamicObservationsInputFiles
    ) -> None:
        """Load observation counts to Loqusdb for a Balsamic case."""
        raise NotImplementedError

    def extract_observations_files_from_hk(
        self, hk_version: Version
    ) -> BalsamicObservationsInputFiles:
        """Extract observations files given a housekeeper version for cancer."""
        raise NotImplementedError

    def delete_case(self, case: models.Family) -> None:
        """Delete cancer case observations from Loqusdb."""
        raise NotImplementedError
