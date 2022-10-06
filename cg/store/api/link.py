"""Module to handle resetting of data in StatusDB."""

from typing import List

from cg.store import models


class LinkHelper:
    """Class that helps handle StatusDB links."""

    @staticmethod
    def is_all_samples_non_tumour(links: List[models.FamilySample]) -> bool:
        """Return True if all samples are non tumour."""
        return all(not link.sample.is_tumour for link in links)

    @staticmethod
    def get_analysis_type_for_each_link(links: List[models.FamilySample]) -> list:
        """Return analysis type for each sample given by link list."""
        return [link.sample.application_version.application.analysis_type for link in links]
