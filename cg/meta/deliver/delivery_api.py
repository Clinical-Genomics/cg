"""Module for deliveries of workflow files"""

import logging
from pathlib import Path
from typing import Iterable

from housekeeper.store.models import File, Version

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import delivery as constants
from cg.constants.constants import DataDelivery
from cg.exc import MissingFilesError
from cg.meta.deliver.utils import (
    create_link,
    get_delivery_case_name,
    get_delivery_dir_path,
    get_case_tags_for_pipeline,
    get_out_path,
    get_sample_out_file_name,
    get_sample_tags_for_pipeline,
    include_file_case,
    include_file_sample,
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

    def set_dry_run(self, dry_run: bool):
        self.dry_run = dry_run

    def set_deliver_failed_samples(self, deliver_failed_samples: bool):
        self.deliver_failed_samples = deliver_failed_samples

    def set_ignore_missing_bundles(self, ignore_missing_bundles: bool):
        self.ignore_missing_bundles = ignore_missing_bundles

    def deliver(self, ticket: str | None, case_id: str | None, pipeline: str) -> None:
        if ticket:
            self._deliver_files_by_ticket(ticket=ticket, pipeline=pipeline)
        elif case_id:
            self._deliver_files_by_case(case_id=case_id, pipeline=pipeline)

    def _deliver_files_by_ticket(self, ticket: str, pipeline: str) -> None:
        cases: list[Case] = self.store.get_cases_by_ticket_id(ticket)
        if not cases:
            LOG.warning(f"Could not find cases for ticket {ticket}")
            return
        for case in cases:
            self.deliver_files(case=case, pipeline=pipeline)

    def _deliver_files_by_case(self, case_id: str, pipeline: str) -> None:
        case: Case | None = self.store.get_case_by_internal_id(case_id)
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

        version: Version = self.hk_api.last_version(case.internal_id)
        out_dir: Path = self._create_delivery_directory(case)
        self._link_case_files(case=case, version=version, pipeline=pipeline, out_dir=out_dir)

    def _link_case_files(self, case: Case, version: Version, pipeline: str, out_dir: Path):
        number_linked_files: int = 0
        sample_ids: set[str] = self._get_sample_ids_for_case(case)
        files: list[Path] = self._get_case_files_from_version(
            version=version, sample_ids=sample_ids, pipeline=pipeline
        )
        for file_path in files:
            out_path: Path = get_out_path(out_dir=out_dir, file=file_path, case=case)
            if create_link(source=file_path, destination=out_path, dry_run=self.dry_run):
                number_linked_files += 1

    def _get_sample_ids_for_case(self, case: Case) -> set[str]:
        links = self.store.get_case_samples_by_case_id(case.internal_id)
        samples: list[Sample] = [link.sample for link in links]
        sample_ids: set[str] = {sample.internal_id for sample in samples}
        return sample_ids

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
        if not get_sample_tags_for_pipeline(pipeline):
            return

        deliverable_samples = self._get_deliverable_samples(case=case, pipeline=pipeline)
        case_name: str | None = get_delivery_case_name(case=case, pipeline=pipeline)
        for link in deliverable_samples:
            delivery_base: Path = self._create_sample_delivery_directory(
                case=case, sample=link.sample, pipeline=pipeline
            )

            number_linked_files: int = 0
            version: Version = self._get_version_for_sample(
                sample=link.sample, case=case, pipeline=pipeline
            )
            sample_id = link.sample.internal_id
            files: list[Path] = self._get_sample_files_from_version(
                version=version, sample_id=sample_id, pipeline=pipeline
            )
            for file_path in files:
                file_name: str = get_sample_out_file_name(file=file_path, sample=link.sample)
                if case_name:
                    file_name: str = file_name.replace(case.internal_id, case.name)
                out_path = Path(delivery_base, file_name)
                if create_link(source=file_path, destination=out_path, dry_run=self.dry_run):
                    number_linked_files += 1

            if not files and number_linked_files == 0:
                raise MissingFilesError(f"Could not find any files for sample {sample_id}")

    def _create_sample_delivery_directory(self, case: Case, sample: Sample, pipeline: str) -> Path:
        case_name: str | None = get_delivery_case_name(case=case, pipeline=pipeline)
        delivery_base = get_delivery_dir_path(
            case_name=case_name,
            sample_name=sample.name,
            customer_id=case.customer.internal_id,
            ticket=case.latest_ticket,
            base_path=self.project_base_path,
        )
        if not self.dry_run:
            LOG.debug(f"Creating project path {delivery_base}")
            delivery_base.mkdir(parents=True, exist_ok=True)
        return delivery_base

    def _get_deliverable_samples(self, case: Case, pipeline: str) -> Iterable[CaseSample]:
        return filter(
            lambda link: self._sample_is_deliverable(link=link, case=case, pipeline=pipeline),
            self.store.get_case_samples_by_case_id(case.internal_id),
        )

    def _get_version_for_sample(self, sample: Sample, case: Case, pipeline: str) -> Version:
        bundle: str = sample.internal_id if pipeline == DataDelivery.FASTQ else case.internal_id
        return self.hk_api.last_version(bundle)

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
            if not include_file_case(file=version_file, sample_ids=sample_ids, pipeline=pipeline):
                LOG.debug(f"Skipping file {version_file.path}")
                continue
            yield Path(version_file.full_path)

    def _get_sample_files_from_version(
        self,
        version: Version,
        sample_id: str,
        pipeline: str,
    ) -> Iterable[Path]:
        """Fetch files for a sample from a version that are tagged with sample tags."""
        file_obj: File
        for file_obj in version.files:
            if not include_file_sample(file=file_obj, sample_id=sample_id, pipeline=pipeline):
                continue
            yield Path(file_obj.full_path)

    def _case_is_deliverable(self, case: Case, pipeline: str) -> bool:
        last_version = self.hk_api.last_version(case.internal_id)
        if not last_version:
            case_tags = get_case_tags_for_pipeline(pipeline)
            skip_missing = pipeline in constants.SKIP_MISSING or self.ignore_missing_bundles
            if not case_tags:
                LOG.info(f"Could not find any version for {case.internal_id}")
            elif not skip_missing:
                raise SyntaxError(f"Could not find any version for {case.internal_id}")
            return False
        return self._case_has_samples(case)

    def _case_has_samples(self, case: Case) -> bool:
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
