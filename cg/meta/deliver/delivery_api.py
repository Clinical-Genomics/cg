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
    get_delivery_case_name,
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
        self.store = store
        self.hk_api = hk_api
        self.project_base_path = project_base_path
        self.ignore_missing_bundles = ignore_missing_bundles
        self.deliver_failed_samples = force_all
        self.dry_run = dry_run

    def deliver(self, ticket: str | None, case_id: str | None, pipeline: str) -> None:
        if ticket:
            self._deliver_files_by_ticket(ticket=ticket, pipeline=pipeline)
        elif case_id:
            self._deliver_files_by_case_id(case_id=case_id, pipeline=pipeline)

    def _deliver_files_by_ticket(self, ticket: str, pipeline: str) -> None:
        cases: list[Case] = self.store.get_cases_by_ticket_id(ticket)
        if not cases:
            LOG.warning(f"Could not find cases for ticket {ticket}")
            return
        for case in cases:
            self.deliver_files(case=case, pipeline=pipeline)

    def _deliver_files_by_case_id(self, case_id: str, pipeline: str) -> None:
        case: Case = self.store.get_case_by_internal_id(case_id)
        if not case:
            LOG.warning(f"Could not find case {case_id}")
            return
        self.deliver_files(case=case, pipeline=pipeline)

    def deliver_files(self, case: Case, pipeline: str):
        if not self._case_is_deliverable(case=case, pipeline=pipeline):
            return
        self._deliver_case_files(case=case, pipeline=pipeline)
        self._deliver_sample_files(case=case, pipeline=pipeline)

    def _deliver_case_files(self, case: Case, pipeline: str) -> None:
        LOG.debug(f"Deliver case files for {case.internal_id}")

        if not get_case_tags_for_pipeline(pipeline):
            return

        version: Version | None = self.hk_api.last_version(case.internal_id)
        if not version:
            LOG.warning(f"No version found for case {case.internal_id}")
            return

        out_dir: Path = self._create_delivery_directory(case)
        self._link_case_files(case=case, version=version, pipeline=pipeline, out_dir=out_dir)

    def _link_case_files(self, case: Case, version: Version, pipeline: str, out_dir: Path):
        file_path: Path
        number_linked_files: int = 0
        sample_ids: set[str] = self._get_sample_ids_for_case(case)
        files: list[Path] = self._get_case_files_from_version(
            version=version, sample_ids=sample_ids, pipeline=pipeline
        )
        for file_path in files:
            out_path: Path = self._get_out_path(out_dir=out_dir, file=file_path, case=case)
            if self._create_link(source=file_path, destination=out_path):
                number_linked_files += 1

    def _get_out_path(self, out_dir: Path, file: Path, case: Case) -> Path:
        out_file_name: str = self._get_out_file_name(file=file, case=case)
        return Path(out_dir, out_file_name)

    def _get_out_file_name(self, file: Path, case: Case) -> str:
        return file.name.replace(case.internal_id, case.name)

    def _get_sample_ids_for_case(self, case: Case) -> set[str]:
        links = self.store.get_case_samples_by_case_id(case.internal_id)
        samples: list[Sample] = [link.sample for link in links]
        sample_ids: set[str] = {sample.internal_id for sample in samples}
        return sample_ids

    def _create_link(self, source: Path, destination: Path) -> bool:
        if self.dry_run:
            LOG.info(f"Would hard link file {source} to {destination}")
            return True
        try:
            os.link(source, destination)
            LOG.info(f"Hard link file {source} to {destination}")
            return True
        except FileExistsError:
            LOG.info(f"Path {destination} exists, skipping")
            return False

    def _create_delivery_directory(self, case: Case) -> Path:
        delivery_base = get_delivery_dir_path(
            case_name=case.name,
            customer_id=case.customer.internal_id,
            ticket=case.latest_ticket,
            base_path=self.project_base_path,
        )
        if not self.dry_run:
            LOG.debug(f"Creating project path {delivery_base}")
            delivery_base.mkdir(parents=True, exist_ok=True)
        return delivery_base

    def _deliver_sample_files(self, case: Case, pipeline: str) -> None:
        """Deliver files on sample level."""
        if not get_sample_tags_for_pipeline(pipeline):
            return

        case_name: str | None = get_delivery_case_name(case=case, pipeline=pipeline)

        deliverable_samples = filter(
            lambda link: self._sample_is_deliverable(link=link, case=case, pipeline=pipeline),
            self.store.get_case_samples_by_case_id(case.internal_id),
        )

        for link in deliverable_samples:
            sample_id = link.sample.internal_id
            sample_name = link.sample.name
            if pipeline == DataDelivery.FASTQ:
                version: Version = self.hk_api.last_version(sample_id)
            else:
                version: Version = self.hk_api.last_version(case.internal_id)
            delivery_base: Path = get_delivery_dir_path(
                case_name=case_name,
                sample_name=sample_name,
                customer_id=case.customer.internal_id,
                ticket=case.latest_ticket,
                base_path=self.project_base_path,
            )
            if not self.dry_run:
                LOG.debug(f"Creating project path {delivery_base}")
                delivery_base.mkdir(parents=True, exist_ok=True)
            file_path: Path
            number_linked_files_now: int = 0
            number_previously_linked_files: int = 0
            for file_path in self._get_sample_files_from_version(
                version=version, sample_id=sample_id, pipeline=pipeline
            ):
                # Out path should include customer names
                file_name: str = file_path.name.replace(sample_id, sample_name)
                if case_name:
                    file_name: str = file_name.replace(case.internal_id, case.name)
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
                f"There were {number_previously_linked_files} previously linked files and {number_linked_files_now} were linked for sample {sample_id}, case {case.internal_id}"
            )

    def _get_case_files_from_version(
        self, version: Version, sample_ids: set[str], pipeline: str
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
        version: Version,
        sample_id: str,
        pipeline: str,
    ) -> Iterable[Path]:
        """Fetch all files for a sample from a version that are tagged with any of the sample
        tags."""
        file_obj: File
        for file_obj in version.files:
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

    def _case_is_deliverable(self, case: Case, pipeline: str) -> bool:
        last_version = self.hk_api.last_version(case.internal_id)
        skip_missing = pipeline in constants.SKIP_MISSING or self.ignore_missing_bundles
        case_tags = get_case_tags_for_pipeline(pipeline)

        if not last_version:
            if not case_tags:
                LOG.info(f"Could not find any version for {case.internal_id}")
            elif not skip_missing:
                raise SyntaxError(f"Could not find any version for {case.internal_id}")
            return False
        return self._samples_are_deliverable(case)

    def _samples_are_deliverable(self, case: Case) -> bool:
        if self.store.get_case_samples_by_case_id(case.internal_id):
            return True
        LOG.warning(f"Could not find any samples linked to case {case.internal_id}")
        return False

    def _sample_is_deliverable(self, link: CaseSample, case: Case, pipeline: str) -> bool:
        sample_is_external: bool = link.sample.application_version.application.is_external
        deliver_failed_samples: bool = self.deliver_failed_samples
        sample_passes_qc: bool = link.sample.sequencing_qc
        sample_is_deliverable: bool = (
            sample_passes_qc or deliver_failed_samples or sample_is_external
        )
        last_version: Version = self.hk_api.last_version(case.internal_id)
        if pipeline == DataDelivery.FASTQ:
            last_version = self.hk_api.last_version(link.sample.internal_id)
        if not last_version:
            skip_missing = pipeline in constants.SKIP_MISSING or self.ignore_missing_bundles
            if skip_missing:
                LOG.info(f"Could not find any version for {link.sample.internal_id}")
                return False
            raise SyntaxError(f"Could not find any version for {link.sample.internal_id}")
        if not sample_is_deliverable:
            LOG.warning(f"Sample {link.sample.internal_id} is not deliverable.")
        return sample_is_deliverable
