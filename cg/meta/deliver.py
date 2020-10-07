"""Module for deliveries of workflow files"""

import logging

from cg.apps.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.store import Store

LOG = logging.getLogger(__name__)


class DeliverAPI:
    """Deliver API for workflows files"""

    def __init__(
        self,
        db: Store,
        hk_api: HousekeeperAPI,
        lims_api: LimsAPI,
        case_tags: [str],
        sample_tags: [str],
    ):
        self.store = db
        self.hk_api = hk_api
        self.lims = lims_api
        self.case_tags = case_tags
        self.sample_tags = sample_tags

    def get_post_analysis_files(self, case: str, version, tags: list):

        if not version:
            last_version = self.hk_api.last_version(bundle=case)
        else:
            last_version = self.hk_api.version(bundle=case, date=version)

        return self.hk_api.files(bundle=case, version=last_version.id, tags=tags).all()

    def get_post_analysis_case_files(self, case: str, version, tags):
        """Link files from HK to cust inbox."""

        tagged_files = self.get_post_analysis_files(case, version, tags)
        case_obj = self.store.family_samples(case)
        sample_ids = [case_sample.sample.internal_id for case_sample in case_obj]

        case_files = []
        for file_obj in tagged_files:

            if any(tag.name in sample_ids for tag in file_obj.tags):
                continue

            if any(tag.name in self.case_tags for tag in file_obj.tags):
                case_files.append(file_obj)

        return case_files

    def get_post_analysis_sample_files(self, case: str, sample: str, version, tag):
        """Link files from HK to cust inbox."""

        all_files = self.get_post_analysis_files(case, version, tag)

        sample_files = []
        for file_obj in all_files:
            if not any(tag.name == sample for tag in file_obj.tags):
                continue

            if any(tag.name in self.sample_tags for tag in file_obj.tags):
                sample_files.append(file_obj)

        return sample_files

    def get_post_analysis_files_root_dir(self):
        return self.hk_api.get_root_dir()
