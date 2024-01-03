"""Module for deliveries of workflow files"""

import logging
import os
from copy import deepcopy
from pathlib import Path
from typing import Iterable

from housekeeper.store.models import File, Version

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import delivery as constants
from cg.constants.constants import DataDelivery
from cg.exc import MissingFilesError
from cg.meta.deliver.utils import (
    get_delivery_dir_path,
    get_case_tags_for_pipeline,
    get_sample_tags_for_pipeline,
)
from cg.store import Store
from cg.store.models import Case, CaseSample, Sample

LOG = logging.getLogger(__name__)


class DeliveryAPI:
    """Deliver API for workflows files."""

    def __init__(
        self,
        store: Store,
        hk_api: HousekeeperAPI,
        project_base_path: Path,
        force_all: bool = False,
        ignore_missing_bundles: bool = False,
        dry_run: bool = False,
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
        self.dry_run = False
        self.ignore_missing_bundles: bool = ignore_missing_bundles
        self.deliver_failed_samples = force_all
        self.dry_run = dry_run

    def deliver_files(self, case: Case, pipeline: str):
        """Deliver all files for a case.

        If there are sample tags deliver all files for the samples as well.
        """
        case_tags: list[set[str]] = get_case_tags_for_pipeline(pipeline)
        sample_tags: list[set[str]] = get_sample_tags_for_pipeline(pipeline)
        self.skip_missing_bundle: bool = (
            pipeline in constants.SKIP_MISSING or self.ignore_missing_bundles
        )
        case_id: str = case.internal_id
        case_name: str = case.name
        customer_id: str = case.customer.internal_id
        ticket: str = case.latest_ticket
        last_version: Version = self.hk_api.last_version(case_id)

        if not last_version:
            if not case_tags:
                LOG.info(f"Could not find any version for {case_id}")
            elif not self.skip_missing_bundle:
                raise SyntaxError(f"Could not find any version for {case_id}")
        links: list[CaseSample] = self.store.get_case_samples_by_case_id(case_id)
        if not links:
            LOG.warning(f"Could not find any samples linked to case {case_id}")
            return
        samples: list[Sample] = [link.sample for link in links]
        sample_ids: set[str] = {sample.internal_id for sample in samples}
        if case_tags:
            self._deliver_case_files(
                case_id=case_id,
                case_name=case_name,
                version=last_version,
                sample_ids=sample_ids,
                customer_id=customer_id,
                ticket=ticket,
                pipeline=pipeline,
            )

        if not sample_tags:
            return

        link: CaseSample
        for link in links:
            if self._sample_is_deliverable(link):
                sample_id: str = link.sample.internal_id
                sample_name: str = link.sample.name
                LOG.debug(f"Fetch last version for sample bundle {sample_id}")
                if pipeline == DataDelivery.FASTQ:
                    last_version: Version = self.hk_api.last_version(sample_id)
                if not last_version:
                    if self.skip_missing_bundle:
                        LOG.info(f"Could not find any version for {sample_id}")
                        continue
                    raise SyntaxError(f"Could not find any version for {sample_id}")
                self._deliver_sample_files(
                    case_id=case_id,
                    case_name=case_name,
                    sample_id=sample_id,
                    sample_name=sample_name,
                    version_obj=last_version,
                    customer_id=customer_id,
                    ticket=ticket,
                    pipeline=pipeline,
                )
                continue
            LOG.warning(f"Sample {link.sample.internal_id} is not deliverable.")

    def _sample_is_deliverable(self, link: CaseSample) -> bool:
        sample_is_external: bool = link.sample.application_version.application.is_external
        deliver_failed_samples: bool = self.deliver_failed_samples
        sample_passes_qc: bool = link.sample.sequencing_qc
        return sample_passes_qc or deliver_failed_samples or sample_is_external

    def _deliver_case_files(
        self,
        case_id: str,
        case_name: str,
        version: Version,
        sample_ids: set[str],
        customer_id: str,
        ticket: str,
        pipeline: str,
    ) -> None:
        """Deliver files on case level."""
        LOG.debug(f"Deliver case files for {case_id}")
        delivery_base: Path = get_delivery_dir_path(
            case_name=case_name,
            customer_id=customer_id,
            ticket=ticket,
            base_path=self.project_base_path,
        )
        if not self.dry_run:
            LOG.debug(f"Creating project path {delivery_base}")
            delivery_base.mkdir(parents=True, exist_ok=True)
        file_path: Path
        number_linked_files: int = 0
        for file_path in self._get_case_files_from_version(
            version=version, sample_ids=sample_ids, pipeline=pipeline
        ):
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

    def _deliver_sample_files(
        self,
        case_id: str,
        case_name: str,
        sample_id: str,
        sample_name: str,
        version_obj: Version,
        customer_id: str,
        ticket: str,
        pipeline: str,
    ) -> None:
        """Deliver files on sample level."""
        # Make sure that the directory exists
        if pipeline in constants.ONLY_ONE_CASE_PER_TICKET:
            case_name = None
        delivery_base: Path = get_delivery_dir_path(
            case_name=case_name,
            sample_name=sample_name,
            customer_id=customer_id,
            ticket=ticket,
            base_path=self.project_base_path,
        )
        if not self.dry_run:
            LOG.debug(f"Creating project path {delivery_base}")
            delivery_base.mkdir(parents=True, exist_ok=True)
        file_path: Path
        number_linked_files_now: int = 0
        number_previously_linked_files: int = 0
        for file_path in self._get_sample_files_from_version(
            version_obj=version_obj, sample_id=sample_id, pipeline=pipeline
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
            raise MissingFilesError(f"No files were linked for sample {sample_name}")

        LOG.info(
            f"There were {number_previously_linked_files} previously linked files and {number_linked_files_now} were linked for sample {sample_id}, case {case_id}"
        )

    def _get_case_files_from_version(
        self,
        version: Version,
        sample_ids: set[str],
        pipeline: str,
    ) -> Iterable[Path]:
        """Fetch all case files from a version that are tagged with any of the case tags."""

        if not version:
            LOG.warning("Version is None, cannot get files")
            return []

        if not version.files:
            LOG.warning(f"No files associated with Housekeeper version {version.id}")
            return []

        version_file: File
        for version_file in version.files:
            if not self._include_file_case(
                file=version_file, sample_ids=sample_ids, pipeline=pipeline
            ):
                LOG.debug(f"Skipping file {version_file.path}")
                continue
            yield Path(version_file.full_path)

    def _get_sample_files_from_version(
        self,
        version_obj: Version,
        sample_id: str,
        pipeline: str,
    ) -> Iterable[Path]:
        """Fetch all files for a sample from a version that are tagged with any of the sample
        tags."""
        file_obj: File
        for file_obj in version_obj.files:
            if not self._include_file_sample(file=file_obj, sample_id=sample_id, pipeline=pipeline):
                continue
            yield Path(file_obj.full_path)

    def _include_file_case(self, file: File, sample_ids: set[str], pipeline: str) -> bool:
        """Check if file should be included in case bundle.

        At least one tag should match between file and tags.
        Do not include files with sample tags.
        """
        file_tags = {tag.name for tag in file.tags}
        case_tags = get_case_tags_for_pipeline(pipeline)
        all_case_tags: set[str] = {tag for tags in case_tags for tag in tags}
        if all_case_tags.isdisjoint(file_tags):
            LOG.debug("No tags are matching")
            return False

        LOG.debug(f"Found file tags {', '.join(file_tags)}")

        # Check if any of the sample tags exist
        if sample_ids.intersection(file_tags):
            LOG.debug(f"Found sample tag, skipping {file.path}")
            return False

        # Check if any of the file tags matches the case tags
        tags: set[str]
        for tags in case_tags:
            LOG.debug(f"check if {tags} is a subset of {file_tags}")
            if tags.issubset(file_tags):
                return True
        LOG.debug(f"Could not find any tags matching file {file.path} with tags {file_tags}")

        return False

    def _include_file_sample(self, file: File, sample_id: str, pipeline: str) -> bool:
        """Check if file should be included in sample bundle.

        At least one tag should match between file and tags.
        Only include files with sample tag.

        For fastq delivery we know that we want to deliver all files of bundle.
        """
        file_tags = {tag.name for tag in file.tags}
        tags: set[str]
        # Check if any of the file tags matches the sample tags
        sample_tags = get_sample_tags_for_pipeline(pipeline)
        for tags in sample_tags:
            working_copy = deepcopy(tags)
            if pipeline != "fastq":
                working_copy.add(sample_id)
            if working_copy.issubset(file_tags):
                return True
        return False

    def set_dry_run(self, dry_run: bool):
        """Set the dry run flag."""
        self.dry_run = dry_run

    def set_force_all(self, force_all: bool):
        """Set the force all flag."""
        self.deliver_failed_samples = force_all

    def set_ignore_missing_bundles(self, ignore_missing_bundles: bool):
        """Set the ignore missing bundles flag."""
        self.ignore_missing_bundles = ignore_missing_bundles
