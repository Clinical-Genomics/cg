"""Module to handle resetting of data in status db."""

import logging

from cg.store import models


LOG = logging.getLogger(__name__)

import logging

LOG = logging.getLogger(__name__)


class ResetHandler:
    """Class to reset records in the status database."""

    def reset_loqusdb_observation_ids(self, case_id: str):
        """Reset links to loqusdb for a case."""

        LOG.info(f"Resetting Loqusdb observations for {case.internal_id}")

        LOG.info("Reseting loqus_id in StatusDB for case: %s", case_id)
        for link in case_obj.links:
            link.sample.loqusdb_id = None
