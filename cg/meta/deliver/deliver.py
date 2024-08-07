"""Module for deliveries of workflow files"""

import logging
import os
from copy import deepcopy
from pathlib import Path
from typing import Iterable

from housekeeper.store.models import File, Version

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import delivery as constants
from cg.constants.constants import DataDelivery, Workflow
from cg.exc import MissingFilesError
from cg.services.fastq_concatenation_service.fastq_concatenation_service import (
    FastqConcatenationService,
)
from cg.services.sequencing_qc_service.sequencing_qc_service import SequencingQCService
from cg.meta.deliver.fastq_path_generator import (
    generate_forward_concatenated_fastq_delivery_path,
    generate_reverse_concatenated_fastq_delivery_path,
)
from cg.store.models import Case, CaseSample, Sample
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class DeliverAPI:
    """Deliver API for workflows files."""

    def __init__(
        self,
        store: Store,
        hk_api: HousekeeperAPI,
        case_tags: list[set[str]],
        sample_tags: list[set[str]],
        project_base_path: Path,
        delivery_type: str,
        fastq_file_service: FastqConcatenationService,
        force_all: bool = False,
        ignore_missing_bundles: bool = False,
    ):
        """Initialize a delivery api

        A delivery is made in the context of a ticket id that can be associated to one or many cases.
        Each case can have one or multiple samples linked to them.

        Each delivery is built around case tags and sample tags. All files tagged will the case_tags will be hard linked
        to the inbox of a customer under <ticket>/<case_id>. All files tagged with sample_tags will be linked to
        <ticket>/<case_id>/<sample_id>.
        """
        self.store = store
        self.hk_api = hk_api
        self.project_base_path: Path = project_base_path
        self.case_tags: list[set[str]] = case_tags
        self.all_case_tags: set[str] = {tag for tags in case_tags for tag in tags}
        self.sample_tags: list[set[str]] = sample_tags
        self.customer_id: str = ""
        self.ticket: str = ""
        self.dry_run = False
        self.delivery_type: str = delivery_type
        self.skip_missing_bundle: bool = (
            self.delivery_type in constants.SKIP_MISSING or ignore_missing_bundles
        )
        self.deliver_failed_samples = force_all
        self.fastq_concatenation_service = fastq_file_service

    def set_dry_run(self, dry_run: bool) -> None:
        """Update dry run."""
        LOG.info(f"Set dry run to {dry_run}")
        self.dry_run = dry_run

    def deliver_files(self, case_obj: Case):
        """Deliver all files for a case.

        If there are sample tags deliver all files for the samples as well.
        """
        case_id: str = case_obj.internal_id
        case_name: str = case_obj.name
        LOG.debug(
            f"Fetch latest version for case {case_id}",
        )
        last_version: Version = self.hk_api.last_version(bundle=case_id)
        if not last_version:
            if not self.case_tags:
                LOG.info(f"Could not find any version for {case_id}")
            elif not self.skip_missing_bundle:
                raise SyntaxError(f"Could not find any version for {case_id}")
        links: list[CaseSample] = self.store.get_case_samples_by_case_id(case_internal_id=case_id)
        if not links:
            LOG.warning(f"Could not find any samples linked to case {case_id}")
            return
        samples: list[Sample] = [link.sample for link in links]
        self.set_ticket(case_obj.latest_ticket)
        self.set_customer_id(case_obj=case_obj)

        sample_ids: set[str] = {sample.internal_id for sample in samples}

        if self.case_tags:
            self.deliver_case_files(
                case_id=case_id,
                case_name=case_name,
                version=last_version,
                sample_ids=sample_ids,
            )

        if not self.sample_tags:
            return

        link: CaseSample
        for link in links:
            if self.is_sample_deliverable(link):
                sample_id: str = link.sample.internal_id
                sample_name: str = link.sample.name
                LOG.debug(f"Fetch last version for sample bundle {sample_id}")
                if self.delivery_type == DataDelivery.FASTQ:
                    last_version: Version = self.hk_api.last_version(bundle=sample_id)
                if not last_version:
                    if self.skip_missing_bundle:
                        LOG.info(f"Could not find any version for {sample_id}")
                        continue
                    raise SyntaxError(f"Could not find any version for {sample_id}")
                self.deliver_sample_files(
                    case=case_obj,
                    sample_id=sample_id,
                    sample_name=sample_name,
                    version_obj=last_version,
                )
                continue
            LOG.warning(
                f"Sample {link.sample.internal_id} did not receive enough reads and will not be delivered"
            )

    def is_sample_deliverable(self, link: CaseSample) -> bool:
        sample_is_external: bool = link.sample.application_version.application.is_external
        deliver_failed_samples: bool = self.deliver_failed_samples
        sample_passes_sequencing_quality_check: bool = (
            SequencingQCService.sample_pass_sequencing_qc(sample=link.sample)
        )

        return (
            sample_passes_sequencing_quality_check or deliver_failed_samples or sample_is_external
        )

    def deliver_case_files(
        self, case_id: str, case_name: str, version: Version, sample_ids: set[str]
    ) -> None:
        """Deliver files on case level."""
        LOG.debug(f"Deliver case files for {case_id}")
        # Make sure that the directory exists
        delivery_base: Path = self.create_delivery_dir_path(case_name=case_name)
        LOG.debug(f"Creating project path {delivery_base}")
        if not self.dry_run:
            delivery_base.mkdir(parents=True, exist_ok=True)
        file_path: Path
        number_linked_files: int = 0
        for file_path in self.get_case_files_from_version(version=version, sample_ids=sample_ids):
            # Out path should include customer names
            out_path: Path = delivery_base / file_path.name.replace(case_id, case_name)
            if out_path.exists():
                LOG.warning(f"File {out_path} already exists!")
                continue

            if self.dry_run:
                LOG.info(f"Would hard link file {file_path} to {out_path}")
                number_linked_files += 1
                continue
            LOG.info(f"Hard link file {file_path} to {out_path}")
            try:
                os.link(file_path, out_path)
                number_linked_files += 1
            except FileExistsError:
                LOG.info(f"Path {out_path} exists, skipping")

        LOG.info(f"Linked {number_linked_files} files for case {case_id}")

    def deliver_sample_files(
        self,
        case: Case,
        sample_id: str,
        sample_name: str,
        version_obj: Version,
    ) -> None:
        """Deliver files on sample level."""
        # Make sure that the directory exists
        case_name: str = case.name
        case_id: str = case.internal_id

        if self.delivery_type in constants.ONLY_ONE_CASE_PER_TICKET:
            case_name = None
        delivery_base: Path = self.create_delivery_dir_path(
            case_name=case_name, sample_name=sample_name
        )
        LOG.debug(f"Creating project path {delivery_base}")
        if not self.dry_run:
            delivery_base.mkdir(parents=True, exist_ok=True)
        file_path: Path
        number_linked_files_now: int = 0
        number_previously_linked_files: int = 0
        for file_path in self.get_sample_files_from_version(
            version_obj=version_obj, sample_id=sample_id
        ):
            # Out path should include customer names
            file_name: str = file_path.name.replace(sample_id, sample_name)
            if case_name:
                file_name: str = file_name.replace(case_id, case_name)
            out_path: Path = delivery_base / file_name
            if self.dry_run:
                LOG.info(f"Would hard link file {file_path} to {out_path}")
                number_linked_files_now += 1
                continue
            LOG.info(f"Hard link file {file_path} to {out_path}")
            try:
                os.link(file_path, out_path)
                number_linked_files_now += 1
            except FileExistsError:
                LOG.info(
                    f"Warning: Path {out_path} exists, no hard link was made for file {file_name}"
                )
                number_previously_linked_files += 1
        if number_previously_linked_files == 0 and number_linked_files_now == 0:
            raise MissingFilesError(f"No files were linked for sample {sample_id} ({sample_name}).")

        LOG.info(
            f"There were {number_previously_linked_files} previously linked files and {number_linked_files_now} were linked for sample {sample_id}, case {case_id}"
        )

        if self.delivery_type == Workflow.FASTQ and case.data_analysis == Workflow.MICROSALT:
            LOG.debug(f"Concatenating fastqs for sample {sample_name}")
            self.concatenate_fastqs(sample_directory=delivery_base, sample_name=sample_name)

    def concatenate_fastqs(self, sample_directory: Path, sample_name: str):
        if self.dry_run:
            return
        forward_output_path: Path = generate_forward_concatenated_fastq_delivery_path(
            fastq_directory=sample_directory, sample_name=sample_name
        )
        reverse_output_path: Path = generate_reverse_concatenated_fastq_delivery_path(
            fastq_directory=sample_directory, sample_name=sample_name
        )
        self.fastq_concatenation_service.concatenate(
            fastq_directory=sample_directory,
            forward_output_path=forward_output_path,
            reverse_output_path=reverse_output_path,
            remove_raw=True,
        )

    def get_case_files_from_version(self, version: Version, sample_ids: set[str]) -> Iterable[Path]:
        """Fetch all case files from a version that are tagged with any of the case tags."""

        if not version:
            LOG.warning("Version is None, cannot get files")
            return []

        if not version.files:
            LOG.warning(f"No files associated with Housekeeper version {version.id}")
            return []

        version_file: File
        for version_file in version.files:
            if not self.include_file_case(file=version_file, sample_ids=sample_ids):
                LOG.debug(f"Skipping file {version_file.path}")
                continue
            yield Path(version_file.full_path)

    def get_sample_files_from_version(self, version_obj: Version, sample_id: str) -> Iterable[Path]:
        """Fetch all files for a sample from a version that are tagged with any of the sample
        tags."""
        file_obj: File
        for file_obj in version_obj.files:
            if not self.include_file_sample(file_obj, sample_id=sample_id):
                continue
            yield Path(file_obj.full_path)

    def include_file_case(self, file: File, sample_ids: set[str]) -> bool:
        """Check if file should be included in case bundle.

        At least one tag should match between file and tags.
        Do not include files with sample tags.
        """
        file_tags = {tag.name for tag in file.tags}
        if self.all_case_tags.isdisjoint(file_tags):
            LOG.debug("No tags are matching")
            return False

        LOG.debug(f"Found file tags {', '.join(file_tags)}")

        # Check if any of the sample tags exist
        if sample_ids.intersection(file_tags):
            LOG.debug(f"Found sample tag, skipping {file.path}")
            return False

        # Check if any of the file tags matches the case tags
        tags: set[str]
        for tags in self.case_tags:
            LOG.debug(f"check if {tags} is a subset of {file_tags}")
            if tags.issubset(file_tags):
                return True
        LOG.debug(f"Could not find any tags matching file {file.path} with tags {file_tags}")

        return False

    def include_file_sample(self, file_obj: File, sample_id: str) -> bool:
        """Check if file should be included in sample bundle.

        At least one tag should match between file and tags.
        Only include files with sample tag.

        For fastq delivery we know that we want to deliver all files of bundle.
        """
        file_tags = {tag.name for tag in file_obj.tags}
        tags: set[str]
        # Check if any of the file tags matches the sample tags
        for tags in self.sample_tags:
            working_copy = deepcopy(tags)
            if self.delivery_type != "fastq":
                working_copy.add(sample_id)
            if working_copy.issubset(file_tags):
                return True

        return False

    def _set_customer_id(self, customer_id: str) -> None:
        LOG.info(f"Setting customer_id to {customer_id}")
        self.customer_id = customer_id

    def set_customer_id(self, case_obj: Case) -> None:
        """Set the customer_id for this upload"""
        self._set_customer_id(case_obj.customer.internal_id)

    def set_ticket(self, ticket: str) -> None:
        """Set the ticket for this upload"""
        LOG.info(f"Setting ticket to {ticket}")
        self.ticket = ticket

    def create_delivery_dir_path(self, case_name: str = None, sample_name: str = None) -> Path:
        """Create a path for delivering files.

        Note that case name and sample name needs to be the identifiers sent from customer.
        """
        delivery_path: Path = Path(
            self.project_base_path, self.customer_id, constants.INBOX_NAME, self.ticket
        )
        if case_name:
            delivery_path = delivery_path / case_name
        if sample_name:
            delivery_path = delivery_path / sample_name

        return delivery_path

    @staticmethod
    def get_delivery_scope(delivery_arguments: set[str]) -> tuple[bool, bool]:
        """Returns the scope of the delivery, ie whether sample and/or case files were delivered."""
        case_delivery: bool = False
        sample_delivery: bool = False
        for delivery in delivery_arguments:
            if (
                constants.PIPELINE_ANALYSIS_TAG_MAP[delivery]["sample_tags"]
                and delivery in constants.ONLY_ONE_CASE_PER_TICKET
            ):
                sample_delivery = True
            if constants.PIPELINE_ANALYSIS_TAG_MAP[delivery]["case_tags"]:
                case_delivery = True
        return sample_delivery, case_delivery
