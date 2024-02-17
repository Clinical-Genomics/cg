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
    get_case_tags_for_workflow,
    get_out_path,
    get_sample_out_file_name,
    get_sample_tags_for_workflow,
    include_file_case,
    should_include_file_sample,
)
from cg.store.store import Store
from cg.store.models import Case, CaseSample, Sample

LOG = logging.getLogger(__name__)


class DeliveryAPI:
    """Deliver API for workflows files."""

    def __init__(
        self,
        store: Store,
        hk_api: HousekeeperAPI,
        customers_folder: Path,
        force_all: bool = False,
        ignore_missing_bundles: bool = False,
        dry_run: bool = False,
    ):
        self.store = store
        self.hk_api = hk_api
        self.customers_folder = customers_folder
        self.ignore_missing_bundles = ignore_missing_bundles
        self.deliver_failed_samples = force_all
        self.dry_run = dry_run

    def deliver(self, ticket: str | None, case_id: str | None, workflow: str) -> None:
        if ticket:
            self._deliver_files_by_ticket(ticket=ticket, workflow=workflow)
        elif case_id:
            self._deliver_files_by_case(case_id=case_id, workflow=workflow)

    def _deliver_files_by_ticket(self, ticket: str, workflow: str) -> None:
        cases: list[Case] = self.store.get_cases_by_ticket_id(ticket)
        if not cases:
            LOG.warning(f"Could not find cases for ticket {ticket}")
            return
        for case in cases:
            self.deliver_files(case=case, workflow=workflow)

    def _deliver_files_by_case(self, case_id: str, workflow: str) -> None:
        case: Case | None = self.store.get_case_by_internal_id(case_id)
        if not case:
            LOG.warning(f"Could not find case {case_id}")
            return
        self.deliver_files(case=case, workflow=workflow)

    def deliver_files(self, case: Case, workflow: str):
        if self._is_case_deliverable(case=case, workflow=workflow):
            self._deliver_case_files(case=case, workflow=workflow)
            self._deliver_sample_files(case=case, workflow=workflow)

    def _deliver_case_files(self, case: Case, workflow: str) -> None:
        LOG.debug(f"Deliver case files for {case.internal_id}")
        if not get_case_tags_for_workflow(workflow):
            return
        self._link_case_files(case=case, workflow=workflow)

    def _link_case_files(self, case: Case, workflow: str):
        out_dir: Path = self._create_delivery_directory(case)
        files: list[Path] = self._get_case_files(workflow=workflow, case=case)
        for file in files:
            out_file: Path = get_out_path(out_dir=out_dir, file=file, case=case)
            create_link(source=file, destination=out_file, dry_run=self.dry_run)

    def _create_delivery_directory(self, case: Case) -> Path:
        delivery_base: Path = get_delivery_dir_path(
            case_name=case.name,
            customer_id=case.customer.internal_id,
            ticket=case.latest_ticket,
            base_path=self.customers_folder,
        )
        if not self.dry_run:
            LOG.debug(f"Creating project path {delivery_base}")
            delivery_base.mkdir(parents=True, exist_ok=True)
        return delivery_base

    def _deliver_sample_files(self, case: Case, workflow: str) -> None:
        if not get_sample_tags_for_workflow(workflow):
            return

        deliverable_samples: list[Sample] = self._get_deliverable_samples(
            case=case, workflow=workflow
        )
        case_name: str | None = get_delivery_case_name(case=case, workflow=workflow)
        for sample in deliverable_samples:
            sample_target_directory: Path = self._create_sample_delivery_directory(
                case=case, sample=sample, workflow=workflow
            )
            number_linked_files: int = 0
            version: Version = self._get_version_for_sample(
                sample=sample, case=case, workflow=workflow
            )
            sample_id = sample.internal_id
            files: Iterable[Path] = self._get_sample_files_from_version(
                version=version, sample_id=sample_id, workflow=workflow
            )
            for file_path in files:
                file_name: str = get_sample_out_file_name(file=file_path, sample=sample)
                if case_name:
                    file_name: str = file_name.replace(case.internal_id, case.name)
                out_path = Path(sample_target_directory, file_name)
                if create_link(source=file_path, destination=out_path, dry_run=self.dry_run):
                    number_linked_files += 1

            if not files and number_linked_files == 0:
                raise MissingFilesError(f"Could not find any files for sample {sample_id}")

    def _create_sample_delivery_directory(self, case: Case, sample: Sample, workflow: str) -> Path:
        case_name: str | None = get_delivery_case_name(case=case, workflow=workflow)
        delivery_base: Path = get_delivery_dir_path(
            case_name=case_name,
            sample_name=sample.name,
            customer_id=case.customer.internal_id,
            ticket=case.latest_ticket,
            base_path=self.customers_folder,
        )
        if not self.dry_run:
            LOG.debug(f"Creating project path {delivery_base}")
            delivery_base.mkdir(parents=True, exist_ok=True)
        return delivery_base

    def _get_deliverable_samples(self, case: Case, workflow: str) -> list[Sample]:
        deliverable_samples: list[CaseSample] = []
        case_samples: list[CaseSample] = self.store.get_case_samples_by_case_id(case.internal_id)
        for link in case_samples:
            if self._is_sample_deliverable(link=link, case=case, workflow=workflow):
                deliverable_samples.append(link.sample)
        return deliverable_samples

    def _get_version_for_sample(self, sample: Sample, case: Case, workflow: str) -> Version:
        bundle: str = sample.internal_id if workflow == DataDelivery.FASTQ else case.internal_id
        return self.hk_api.last_version(bundle)

    def _get_case_files(self, case: Case, workflow: str) -> Iterable[Path]:
        version: Version = self.hk_api.last_version(case.internal_id)
        sample_ids: set[str] = self._get_sample_ids_for_case(case)

        if not version or not version.files:
            return []

        case_files: list[Path] = []
        for file in version.files:
            if include_file_case(file=file, sample_ids=sample_ids, workflow=workflow):
                case_files.append(Path(file.full_path))
        return case_files

    def _get_sample_ids_for_case(self, case: Case) -> set[str]:
        links = self.store.get_case_samples_by_case_id(case.internal_id)
        samples: list[Sample] = [link.sample for link in links]
        sample_ids: set[str] = {sample.internal_id for sample in samples}
        return sample_ids

    def _get_sample_files_from_version(
        self,
        version: Version,
        sample_id: str,
        workflow: str,
    ) -> Iterable[Path]:
        """Fetch files for a sample from a version that are tagged with sample tags."""
        file_obj: File
        for file_obj in version.files:
            if not should_include_file_sample(
                file=file_obj, sample_id=sample_id, workflow=workflow
            ):
                continue
            yield Path(file_obj.full_path)

    def _is_case_deliverable(self, case: Case, workflow: str) -> bool:
        last_version = self.hk_api.last_version(case.internal_id)
        if not last_version:
            case_tags = get_case_tags_for_workflow(workflow)
            skip_missing = workflow in constants.SKIP_MISSING or self.ignore_missing_bundles
            if not case_tags:
                LOG.info(f"Could not find any version for {case.internal_id}")
            elif not skip_missing:
                raise SyntaxError(f"Could not find any version for {case.internal_id}")
            return False
        return True

    def _is_sample_deliverable(self, link: CaseSample, case: Case, workflow: str) -> bool:
        sample_is_external: bool = link.sample.application_version.application.is_external
        deliver_failed_samples: bool = self.deliver_failed_samples
        sample_passes_qc: bool = link.sample.sequencing_qc
        sample_is_deliverable: bool = (
            sample_passes_qc or deliver_failed_samples or sample_is_external
        )
        last_version: Version = self.hk_api.last_version(case.internal_id)
        if workflow == DataDelivery.FASTQ:
            last_version = self.hk_api.last_version(link.sample.internal_id)
        if not last_version:
            skip_missing = workflow in constants.SKIP_MISSING or self.ignore_missing_bundles
            if skip_missing:
                LOG.info(f"Could not find any version for {link.sample.internal_id}")
                return False
            raise SyntaxError(f"Could not find any version for {link.sample.internal_id}")
        if not sample_is_deliverable:
            LOG.warning(f"Sample {link.sample.internal_id} is not deliverable.")
        return sample_is_deliverable
