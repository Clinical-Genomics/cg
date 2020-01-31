"""Module for deliveries for workflows"""

import logging

from cg.apps import hk, lims
from cg.store import Store

LOG = logging.getLogger(__name__)


class DeliverAPI:
    """Deliver API for workflows"""

    def __init__(
        self, db: Store, hk_api: hk.HousekeeperAPI, lims_api: lims.LimsAPI, family_tags
    ):
        self.store = db
        self.hk_api = hk_api
        self.lims = lims_api
        self.family_tags = family_tags
        self.family_tags = family_tags

    def get_post_analysis_files(self, family: str, version, tags: list):

        if not version:
            last_version = self.hk_api.last_version(bundle=family)
        else:
            last_version = self.hk_api.version(bundle=family, date=version)

        return self.hk_api.files(
            bundle=family, version=last_version.id, tags=tags
        ).all()

    def get_post_analysis_family_files(self, family: str, version, tags):
        """Link files from HK to cust inbox."""

        tagged_files = self.get_post_analysis_files(family, version, tags)
        print(tagged_files)
        family_obj = self.store.family_samples(family)
        print(family_obj)
        sample_ids = [family_sample.sample.internal_id for family_sample in family_obj]
        print(sample_ids)

        family_files = []
        for file_obj in tagged_files:

            print(file_obj)

            if any(tag.name in sample_ids for tag in file_obj.tags):
                continue

            if any(tag.name in self.family_tags for tag in file_obj.tags):
                family_files.append(file_obj)

        return family_files

    def get_post_analysis_sample_files(self, family: str, sample: str, version, tag):
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
