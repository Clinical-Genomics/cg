"""Module for deliveries of workflow files"""

import logging

from datetime import datetime
from typing import List, Iterable
from pathlib import Path

from cg.apps.hk import HousekeeperAPI
from cg.store import Store
from cg.store.models import Family

from housekeeper.store import models as hk_models

LOG = logging.getLogger(__name__)
PROJECT_BASE_PATH = Path("/home/proj/production/customers")


class DeliverAPI:
    """Deliver API for workflows files"""

    def __init__(
        self,
        store: Store,
        hk_api: HousekeeperAPI,
        case_tags: List[str],
        sample_tags: List[str],
        project_base_path: Path = None,
    ):
        """Initialize a delivery api

        A delivery is made in the context of a ticket id that can be associated to one or many cases.
        Each case can have one or multiple samples linked to them.

        Each delivery is built around case tags and sample tags. All files tagged will the case_tags will be hard linked
        to the inbox of a customer under <ticket_nr>/<case_id>. All files tagged with sample_tags will be linked to
        <ticket_nr>/<case_id>/<sample_id>
        """
        self.store = store
        self.hk_api = hk_api
        self.project_base_path = project_base_path or PROJECT_BASE_PATH
        self.case_tags = case_tags
        self.sample_tags = sample_tags
        self.customer_id: str = None
        self.ticket_id: str = None

    def deliver_case_files(self, case_obj: Family):
        """Deliver files on case level"""

    def get_cases(self, ticket_id: int = None, case_id: str = None) -> List[Family]:
        """Fetch cases based on ticket id or case id"""
        if not ticket_id or case_id:
            LOG.error("Provide ticket_id or case_id")
            raise SyntaxError()
        if case_id:
            case_obj: Family = self.store.family(case_id)
            if case_obj is None:
                LOG.warning("Could not find case %s", case_id)
                return None
            return [case_obj]
        return []

    def set_customer_id(self, case_obj: Family) -> None:
        """Set the customer id for this upload"""
        self.customer_id = case_obj.customer.internal_id

    def get_post_analysis_files(
        self, case: str, version: datetime = None, tags: List[str] = None
    ) -> List[Path]:

        if not version:
            last_version: hk_models.Version = self.hk_api.last_version(bundle=case)
        else:
            last_version: hk_models.Version = self.hk_api.version(bundle=case, date=version)

        files = [
            Path(hk_file.full_path)
            for hk_file in self.hk_api.files(bundle=case, version=last_version.id, tags=tags).all()
        ]

        return files

    def get_post_analysis_case_files(self, case: str, version, tags):
        """Fetch files on that """

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
