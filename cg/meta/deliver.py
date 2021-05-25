"""Module for deliveries of workflow files"""

import logging
import os
from copy import deepcopy
from pathlib import Path
from typing import Iterable, List, Set

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import delivery as constants
from cg.store import Store
from cg.store.models import Family, FamilySample, Sample
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
        delivery_type: str,
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
        self.all_case_tags: Set[str] = {tag for tags in case_tags for tag in tags}
        self.sample_tags: List[Set[str]] = sample_tags
        self.customer_id: str = ""
        self.ticket_id: str = ""
        self.dry_run = False
        self.delivery_type: str = delivery_type
        self.skip_missing_bundle = self.delivery_type in constants.SKIP_MISSING

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
        LOG.debug("Fetch latest version for case %s", case_id)
        last_version: hk_models.Version = self.hk_api.last_version(bundle=case_id)
        if not last_version and not self.case_tags:
            LOG.info("Could not find any version for {}".format(case_id))
        elif not last_version and self.skip_missing_bundle == False:
            raise SyntaxError("Could not find any version for {}".format(case_id))
        link_objs: List[FamilySample] = self.store.family_samples(case_id)
        if not link_objs:
            LOG.warning("Could not find any samples linked to case %s", case_id)
            return
        samples: List[Sample] = [link.sample for link in link_objs]
        if not self.ticket_id:
            self.set_ticket_id(sample_obj=samples[0])
        if not self.customer_id:
            self.set_customer_id(case_obj=case_obj)

        sample_ids: Set[str] = {sample.internal_id for sample in samples}

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
            LOG.debug("Fetch last version for sample bundle %s", sample_id)
            if self.delivery_type == "fastq":
                last_version: hk_models.Version = self.hk_api.last_version(bundle=sample_id)
            if not last_version:
                if self.skip_missing_bundle:
                    LOG.info("Could not find any version for {}".format(sample_id))
                    continue
                raise SyntaxError("Could not find any version for {}".format(sample_id))
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
        number_linked_files: int = 0
        for file_path in self.get_case_files_from_version(
            version_obj=version_obj, sample_ids=sample_ids
        ):
            # Out path should include customer names
            out_path: Path = delivery_base / file_path.name.replace(case_id, case_name)
            if out_path.exists():
                LOG.warning("File %s already exists!", out_path)
                continue

            if self.dry_run:
                LOG.info("Would hard link file %s to %s", file_path, out_path)
                number_linked_files += 1
                continue
            LOG.info("Hard link file %s to %s", file_path, out_path)
            try:
                os.link(file_path, out_path)
                number_linked_files += 1
            except FileExistsError:
                LOG.info("Path %s exists, skipping", out_path)

        LOG.info("Linked %s files for case %s", number_linked_files, case_id)

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
        if self.delivery_type in constants.ONLY_ONE_CASE_PER_TICKET:
            case_name = None
        delivery_base: Path = self.create_delivery_dir_path(
            case_name=case_name, sample_name=sample_name
        )
        LOG.debug("Creating project path %s", delivery_base)
        if not self.dry_run:
            delivery_base.mkdir(parents=True, exist_ok=True)
        file_path: Path
        number_linked_files: int = 0
        for file_path in self.get_sample_files_from_version(
            version_obj=version_obj, sample_id=sample_id
        ):
            # Out path should include customer names
            file_name: str = file_path.name.replace(sample_id, sample_name)
            if case_name:
                file_name: str = file_name.replace(case_id, case_name)
            out_path: Path = delivery_base / file_name
            if self.dry_run:
                LOG.info("Would hard link file %s to %s", file_path, out_path)
                number_linked_files += 1
                continue
            LOG.info("Hard link file %s to %s", file_path, out_path)
            try:
                os.link(file_path, out_path)
                number_linked_files += 1
            except FileExistsError:
                LOG.info("Path %s exists, skipping", out_path)
        LOG.info("Linked %s files for sample %s, case %s", number_linked_files, sample_id, case_id)

    def get_case_files_from_version(
        self, version_obj: hk_models.Version, sample_ids: Set[str]
    ) -> Iterable[Path]:
        """Fetch all case files from a version that are tagged with any of the case tags"""
        file_obj: hk_models.File
        for file_obj in version_obj.files:
            if not self.include_file_case(file_obj, sample_ids=sample_ids):
                LOG.debug("Skipping file %s", file_obj.path)
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
        file_tags = {tag.name for tag in file_obj.tags}
        if self.all_case_tags.isdisjoint(file_tags):
            LOG.debug("No tags are matching")
            return False

        LOG.debug("Found file tags %s", ", ".join(file_tags))

        # Check if any of the sample tags exist
        if sample_ids.intersection(file_tags):
            LOG.debug("Found sample tag, skipping %s", file_obj.path)
            return False

        # Check if any of the file tags matches the case tags
        tags: Set[str]
        for tags in self.case_tags:
            LOG.debug("check if %s is a subset of %s", tags, file_tags)
            if tags.issubset(file_tags):
                return True
        LOG.debug("Could not find any tags matching file %s with tags %s", file_obj.path, file_tags)

        return False

    def include_file_sample(self, file_obj: hk_models.File, sample_id: str) -> bool:
        """Check if file should be included in sample bundle

        At least one tag should match between file and tags.
        Only include files with sample tag.

        For fastq delivery we know that we want to deliver all files of bundle
        """
        tag: hk_models.Tag
        file_tags = {tag.name for tag in file_obj.tags}
        tags: Set[str]
        # Check if any of the file tags matches the sample tags
        for tags in self.sample_tags:
            working_copy = deepcopy(tags)
            if self.delivery_type != "fastq":
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

    def create_delivery_dir_path(self, case_name: str = None, sample_name: str = None) -> Path:
        """Create a path for delivering files

        Note that case name and sample name needs to be the identifiers sent from customer
        """
        delivery_path = self.project_base_path / self.customer_id / "inbox" / self.ticket_id
        if case_name:
            delivery_path = delivery_path / case_name
        if sample_name:
            delivery_path = delivery_path / sample_name

        return delivery_path
