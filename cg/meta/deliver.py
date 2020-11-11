"""Module for deliveries of workflow files"""

import logging
import os

from typing import List, Set, Iterable
from pathlib import Path
from copy import deepcopy

from cg.store import Store
from cg.apps.hk import HousekeeperAPI
from cg.store.models import Family, Sample, FamilySample

from housekeeper.store import models as hk_models

LOG = logging.getLogger(__name__)


class DeliverAPI:
    """Deliver API for workflows files"""

    def __init__(
        self,
        store: Store,
        hk_api: HousekeeperAPI,
        case_tags: List[Set[str]],
        sample_tags: List[Set[str]],
        project_base_path: Path,
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
        self.project_base_path: Path = project_base_path
        self.case_tags: List[Set[str]] = case_tags
        self.sample_tags: List[Set[str]] = sample_tags
        self.customer_id: str = ""
        self.ticket_id: str = ""
        self.dry_run = False

    def set_dry_run(self, dry_run: bool) -> None:
        """Update dry run"""
        LOG.info("Set dry run to %s", dry_run)
        self.dry_run = dry_run

    def deliver_files(self, case_obj: Family):
        """Deliver all files for a case

        If there are sample tags deliver all files for the samples as well
        """
        case_id: str = case_obj.internal_id
        case_name: str = case_obj.name
        last_version: hk_models.Version = self.hk_api.last_version(bundle=case_id)
        link_objs: List[FamilySample] = self.store.family_samples(case_id)
        if not link_objs:
            LOG.warning("Could not find any samples linked to case %s", case_id)
            return
        samples: List[Sample] = [link.sample for link in link_objs]
        if not self.ticket_id:
            self.set_ticket_id(sample_obj=samples[0])
        if not self.customer_id:
            self.set_customer_id(case_obj=case_obj)

        sample_ids: Set[str] = set([sample.internal_id for sample in samples])

        if self.case_tags:
            self.deliver_case_files(
                case_id=case_id,
                case_name=case_name,
                version_obj=last_version,
                sample_ids=sample_ids,
            )

        if not self.sample_tags:
            return

        link_obj: FamilySample
        for link_obj in link_objs:
            sample_id: str = link_obj.sample.internal_id
            sample_name: str = link_obj.sample.name
            self.deliver_sample_files(
                case_id=case_id,
                case_name=case_name,
                sample_id=sample_id,
                sample_name=sample_name,
                version_obj=last_version,
            )

    def deliver_case_files(
        self, case_id: str, case_name: str, version_obj: hk_models.Version, sample_ids: Set[str]
    ) -> None:
        """Deliver files on case level"""
        LOG.debug("Deliver case files for %s", case_id)
        # Make sure that the directory exists
        delivery_base: Path = self.create_delivery_dir_path(case_name=case_name)
        LOG.debug("Creating project path %s", delivery_base)
        if not self.dry_run:
            delivery_base.mkdir(parents=True, exist_ok=True)
        file_path: Path
        nr_files: int = 0
        for nr_files, file_path in enumerate(
            self.get_case_files_from_version(version_obj=version_obj, sample_ids=sample_ids), 1
        ):
            # Out path should include customer names
            out_path: Path = delivery_base / file_path.name.replace(case_id, case_name)
            if self.dry_run:
                LOG.info("Would hard link file %s to %s", file_path, out_path)
                continue
            LOG.info("Hard link file %s to %s", file_path, out_path)
            os.link(file_path, out_path)
        LOG.info("Linked %s files for case %s", nr_files, case_id)

    def deliver_sample_files(
        self,
        case_id: str,
        case_name: str,
        sample_id: str,
        sample_name: str,
        version_obj: hk_models.Version,
    ) -> None:
        """Deliver files on sample level"""
        # Make sure that the directory exists
        delivery_base: Path = self.create_delivery_dir_path(
            case_name=case_name, sample_name=sample_name
        )
        LOG.debug("Creating project path %s", delivery_base)
        if not self.dry_run:
            delivery_base.mkdir(parents=True, exist_ok=True)
        file_path: Path
        nr_files: int = 0
        for nr_files, file_path in enumerate(
            self.get_sample_files_from_version(version_obj=version_obj, sample_id=sample_id), 1
        ):
            # Out path should include customer names
            out_path: Path = delivery_base / file_path.name.replace(case_id, case_name).replace(
                sample_id, sample_name
            )
            if self.dry_run:
                LOG.info("Would hard link file %s to %s", file_path, out_path)
                continue
            LOG.info("Hard link file %s to %s", file_path, out_path)
            os.link(file_path, out_path)
        LOG.info("Linked %s files for sample %s, case %s", nr_files, sample_id, case_id)

    def get_case_files_from_version(
        self, version_obj: hk_models.Version, sample_ids: Set[str]
    ) -> Iterable[Path]:
        """Fetch all case files from a version that are tagged with any of the case tags"""
        file_obj: hk_models.File
        for file_obj in version_obj.files:
            if not self.include_file_case(file_obj, sample_ids=sample_ids):
                continue
            yield Path(file_obj.full_path)

    def get_sample_files_from_version(
        self, version_obj: hk_models.Version, sample_id: str
    ) -> Iterable[Path]:
        """Fetch all files for a sample from a version that are tagged with any of the sample tags"""
        file_obj: hk_models.File
        for file_obj in version_obj.files:
            if not self.include_file_sample(file_obj, sample_id=sample_id):
                continue
            yield Path(file_obj.full_path)

    def include_file_case(self, file_obj: hk_models.File, sample_ids: Set[str]) -> bool:
        """Check if file should be included in case bundle

        At least one tag should match between file and tags.
        Do not include files with sample tags.
        """
        tag: hk_models.Tag
        file_tags = set([tag.name for tag in file_obj.tags])

        # Check if any of the sample tags exist
        if not sample_ids.isdisjoint(file_tags):
            return False

        # Check if any of the file tags matches the case tags
        tags: Set[str]
        for tags in self.case_tags:
            if tags.issubset(file_tags):
                return True

        return False

    def include_file_sample(self, file_obj: hk_models.File, sample_id: str) -> bool:
        """Check if file should be included in sample bundle

        At least one tag should match between file and tags.
        Only include files with sample tag.
        """
        tag: hk_models.Tag
        file_tags = set([tag.name for tag in file_obj.tags])
        tags: Set[str]
        # Check if any of the file tags matches the sample tags
        for tags in self.sample_tags:
            working_copy = deepcopy(tags)
            working_copy.add(sample_id)
            if working_copy.issubset(file_tags):
                return True

        return False

    def _set_customer_id(self, customer_id: str) -> None:
        LOG.info("Setting customer_id to %s", customer_id)
        self.customer_id = customer_id

    def _set_ticket_id(self, ticket_nr: int) -> None:
        LOG.info("Setting ticket_id to %s", ticket_nr)
        self.ticket_id = str(ticket_nr)

    def set_customer_id(self, case_obj: Family) -> None:
        """Set the customer_id for this upload"""
        self._set_customer_id(case_obj.customer.internal_id)

    def set_ticket_id(self, sample_obj: Sample) -> None:
        """Set the ticket_id for this upload"""
        self._set_ticket_id(sample_obj.ticket_number)

    def create_delivery_dir_path(self, case_name: str, sample_name: str = None) -> Path:
        """Create a path for delivering files

        Note that case name and sample name needs to be the identifiers sent from customer
        """
        delivery_path = (
            self.project_base_path / self.customer_id / "inbox" / self.ticket_id / case_name
        )
        if sample_name:
            delivery_path = delivery_path / sample_name

        return delivery_path
