"""Module to handle reseting of data in status db"""


class ResetHandler:
    """Class to reset things in the status database"""

    def reset_observations(self, case_id: str):
        """Reset links to loqusdb for a case."""

        family_obj = self.family(case_id)

        for link in family_obj.links:
            link.sample.loqusdb_id = None
