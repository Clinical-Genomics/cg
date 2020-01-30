"""Module for deliveries for workflows"""

import logging

from cg.apps import hk, lims
from cg.store import Store

LOG = logging.getLogger(__name__)


class DeliverAPI:
    """Deliver API for workflows"""

    def __init__(self, db: Store, hk_api: hk.HousekeeperAPI, lims_api: lims.LimsAPI):
        self.store = db
        self.hk_api = hk_api
        self.lims = lims_api

    def get_post_analysis_files(self, family: str, version, tags: list):

        if not version:
            last_version = self.hk_api.last_version(bundle=family)
        else:
            last_version = self.hk_api.version(bundle=family, date=version)

        return self.hk_api.files(
            bundle=family, version=last_version.id, tags=tags
        ).all()

    def get_post_analysis_family_files(
        self, family: str, family_tags: list, version, tags
    ):
        """Link files from HK to cust inbox."""

        all_files = self.get_post_analysis_files(family, version, tags)
        family_obj = self.store.family_samples(family)
        sample_ids = [family_sample.sample.internal_id for family_sample in family_obj]

        family_files = []
        for file_obj in all_files:
            if any(tag.name in sample_ids for tag in file_obj.tags):
                continue

            if any(tag.name in family_tags for tag in file_obj.tags):
                family_files.append(file_obj)

        return family_files

    def get_post_analysis_sample_files(
        self, family: str, sample: str, sample_tags: list, version, tag
    ):
        """Link files from HK to cust inbox."""

        all_files = self.get_post_analysis_files(family, version, tag)

        sample_files = []
        for file_obj in all_files:
            if not any(tag.name == sample for tag in file_obj.tags):
                continue

            if any(tag.name in sample_tags for tag in file_obj.tags):
                sample_files.append(file_obj)

        return sample_files

    def get_post_analysis_files_root_dir(self):
        return self.hk_api.get_root_dir()
