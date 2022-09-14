"""Module to handle resetting of data in status db"""

import logging

from cg.store import models


LOG = logging.getLogger(__name__)


class ResetHandler:
    """Class to reset records in the status database."""

    @staticmethod
    def reset_observations(case: models.Family):
        """Reset links to loqusdb for a case."""

        LOG.info(f"Resetting Loqusdb observations for {case.internal_id}")

        for link in case.links:
            link.sample.loqusdb_id = None
