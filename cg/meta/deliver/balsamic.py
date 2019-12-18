"""Module for deliveries for balsamic"""

import logging

from cg.apps import hk, lims
from cg.store import Store

LOG = logging.getLogger(__name__)

FAMILY_TAGS = [
    "vcf-clinical-sv-bin",
    "vcf-clinical-sv-bin-index",
    "vcf-research-sv-bin",
    "vcf-research-sv-bin-index",
    "gbcf",
    "gbcf-index",
    "snv-gbcf",
    "snv-gbcf-index",
    "snv-bcf",
    "snv-bcf-index",
    "sv-bcf",
    "sv-bcf-index",
    "vcf-snv-clinical",
    "vcf-snv-clinical-index",
    "vcf-snv-research",
    "vcf-snv-research-index",
    "vcf-sv-clinical",
    "vcf-sv-clinical-index",
    "vcf-sv-research",
    "vcf-sv-research-index",
]

SAMPLE_TAGS = ["bam", "bam-index"]


class DeliverAPI:
    """Deliver API for Balsamic"""

    def __init__(self, db: Store, hk_api: hk.HousekeeperAPI, lims_api: lims.LimsAPI):
        self.store = db
        self.hk_api = hk_api
        self.lims = lims_api

    def get_post_analysis_files(self, family: str, version, tags: list):
        """Gets post analysis files"""

        if not version:
            last_version = self.hk_api.last_version(bundle=family)
        else:
            last_version = self.hk_api.version(bundle=family, date=version)

        return self.hk_api.files(
            bundle=family, version=last_version.id, tags=tags
        ).all()

    def get_post_analysis_family_files(self, family: str, version, tags):
        """Link files from HK to cust inbox."""

        all_files = self.get_post_analysis_files(family, version, tags)
        family_obj = self.store.family_samples(family)
        sample_ids = [family_sample.sample.internal_id for family_sample in family_obj]

        family_files = []
        for file_obj in all_files:
            if any(tag.name in sample_ids for tag in file_obj.tags):
                continue

            if any(tag.name in FAMILY_TAGS for tag in file_obj.tags):
                family_files.append(file_obj)

        return family_files

    def get_post_analysis_sample_files(self, family: str, sample: str, version, tag):
        """Link files from HK to cust inbox."""

        all_files = self.get_post_analysis_files(family, version, tag)

        sample_files = []
        for file_obj in all_files:
            if not any(tag.name == sample for tag in file_obj.tags):
                continue

            if any(tag.name in SAMPLE_TAGS for tag in file_obj.tags):
                sample_files.append(file_obj)

        return sample_files

    def get_post_analysis_files_root_dir(self):
        return self.hk_api.get_root_dir()
