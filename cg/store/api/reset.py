"""Module to handle resetting of data in StatusDB."""

import logging

LOG = logging.getLogger(__name__)


class ResetHandler:
    """Class to reset things in the status database."""

    def reset_loqusdb_observation_ids(self, case_id: str):
        """Reset links to Loqusdb for a case."""

        case_obj = self.family(case_id)

        LOG.info("Resetting Loqus ID in StatusDB for case: %s", case_id)
        for link in case_obj.links:
            link.sample.loqusdb_id = None
