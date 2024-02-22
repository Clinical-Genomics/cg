import logging
from pathlib import Path

from housekeeper.store.models import Version
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import delivery as constants
from cg.constants.constants import DataDelivery, Workflow
from cg.exc import MissingFilesError
from cg.meta.deliver.utils import (
    create_link,
    get_bundle_name,
    get_delivery_case_name,
    get_delivery_dir_path,
    get_case_tags_for_workflow,
    get_out_path,
    get_sample_out_file_name,
    get_sample_tags_for_workflow,
    should_include_file_case,
    should_include_file_sample,
)
from cg.services.fastq_file_service.fastq_file_service import FastqFileService
from cg.store.store import Store
from cg.store.models import Case, Sample

LOG = logging.getLogger(__name__)


class DeliveryAPI:
    """In this module, delivery means linking files in a bundle to the customers folder on the compute cluster."""

    def __init__(
        self,
        store: Store,
        hk_api: HousekeeperAPI,
        customers_folder: Path,
        fastq_file_service: FastqFileService,
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
        self.fastq_file_service = fastq_file_service

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
        out_dir: Path = self._create_case_delivery_directory(case)
        files: list[Path] = self._get_case_files(workflow=workflow, case=case)
        for file in files:
            out_file: Path = get_out_path(out_dir=out_dir, file=file, case=case)
            create_link(source=file, destination=out_file, dry_run=self.dry_run)

    def _create_case_delivery_directory(self, case: Case) -> Path:
        case_target_directory: Path = get_delivery_dir_path(
            case_name=case.name,
            customer_id=case.customer.internal_id,
            ticket=case.latest_ticket,
            base_path=self.customers_folder,
        )
        if not self.dry_run:
            LOG.debug(f"Creating delivery directory for case {case_target_directory}")
            case_target_directory.mkdir(parents=True, exist_ok=True)
        return case_target_directory

    def _deliver_sample_files(self, case: Case, workflow: str) -> None:
        if not get_sample_tags_for_workflow(workflow):
            return

        deliverable_samples: list[Sample] = self._get_deliverable_samples(
            case=case, workflow=workflow
        )
        case_name: str | None = get_delivery_case_name(case=case, workflow=workflow)
        for sample in deliverable_samples:
            sample_directory: Path = self._create_sample_delivery_directory(
                case=case, sample=sample, workflow=workflow
            )
            number_linked_files: int = 0
            version: Version = self._get_version_for_sample(
                sample=sample, case=case, workflow=workflow
            )
            files: list[Path] = self._get_sample_files_from_version(
                version=version, workflow=workflow
            )
            for file_path in files:
                file_name: str = get_sample_out_file_name(file=file_path, sample=sample)
                if case_name:
                    file_name: str = file_name.replace(case.internal_id, case.name)
                out_path = Path(sample_directory, file_name)
                if create_link(source=file_path, destination=out_path, dry_run=self.dry_run):
                    number_linked_files += 1

            if not files and number_linked_files == 0:
                raise MissingFilesError(f"Could not find any files for sample {sample.internal_id}")
            if workflow == Workflow.FASTQ and case.data_analysis == Workflow.MICROSALT:
                self.concatenate_fastqs(sample_directory=sample_directory, sample_name=sample.name)

    def _create_sample_delivery_directory(self, case: Case, sample: Sample, workflow: str) -> Path:
        case_name: str | None = get_delivery_case_name(case=case, workflow=workflow)
        sample_directory: Path = get_delivery_dir_path(
            case_name=case_name,
            sample_name=sample.name,
            customer_id=case.customer.internal_id,
            ticket=case.latest_ticket,
            base_path=self.customers_folder,
        )
        if not self.dry_run:
            LOG.debug(f"Creating sample delivery directory {sample_directory}")
            sample_directory.mkdir(parents=True, exist_ok=True)
        return sample_directory

    def _get_deliverable_samples(self, case: Case, workflow: str) -> list[Sample]:
        deliverable_samples: list[Sample] = []
        samples: list[Sample] = self.store.get_samples_by_case_id(case.internal_id)
        for sample in samples:
            bundle_name: str = get_bundle_name(case=case, sample=sample, workflow=workflow)
            bundle_exists: bool = self._bundle_exists(bundle_name=bundle_name, workflow=workflow)
            sample_is_deliverable: bool = self._is_sample_deliverable(sample)
            if bundle_exists and sample_is_deliverable:
                deliverable_samples.append(sample)
        return deliverable_samples

    def _get_version_for_sample(self, sample: Sample, case: Case, workflow: str) -> Version:
        bundle: str = sample.internal_id if workflow == DataDelivery.FASTQ else case.internal_id
        return self.hk_api.last_version(bundle)

    def _get_case_files(self, case: Case, workflow: str) -> list[Path]:
        version: Version = self.hk_api.last_version(case.internal_id)
        sample_ids: set[str] = self._get_sample_ids_for_case(case)

        if not version or not version.files:
            return []

        case_files: list[Path] = []
        for file in version.files:
            if should_include_file_case(file=file, sample_ids=sample_ids, workflow=workflow):
                case_files.append(Path(file.full_path))
        return case_files

    def _get_sample_ids_for_case(self, case: Case) -> set[str]:
        samples: list[Sample] = self.store.get_samples_by_case_id(case.internal_id)
        sample_ids: set[str] = {sample.internal_id for sample in samples}
        return sample_ids

    def _get_sample_files_from_version(
        self,
        version: Version,
        workflow: str,
    ) -> list[Path]:
        """Fetch files for a sample from a version that are tagged with sample tags."""
        sample_files: list[Path] = []
        for file in version.files:
            if should_include_file_sample(file=file, workflow=workflow):
                sample_files.append(Path(file.full_path))
        return sample_files

    def _is_case_deliverable(self, case: Case, workflow: str) -> bool:
        bundle_name: str = case.internal_id
        return self._bundle_exists(bundle_name=bundle_name, workflow=workflow)

    def _is_sample_deliverable(self, sample: Sample) -> bool:
        return (
            sample.sequencing_qc
            or self.deliver_failed_samples
            or sample.application_version.application.is_external
        )

    def _bundle_exists(self, bundle_name: str, workflow: str) -> bool:
        if self.hk_api.last_version(bundle_name):
            return True
        if self.ignore_missing_bundle(workflow):
            return False
        raise SyntaxError(f"Could not find any version for {bundle_name}")

    def ignore_missing_bundle(self, workflow: str) -> bool:
        return workflow in constants.SKIP_MISSING or self.ignore_missing_bundles

    def concatenate_fastqs(self, sample_directory: Path, sample_name: str):
        if self.dry_run:
            return
        forward_out_path = Path(sample_directory, f"{sample_name}_R1.fastq.gz")
        reverse_out_path = Path(sample_directory, f"{sample_name}_R2.fastq.gz")
        self.fastq_file_service.concatenate(
            fastq_directory=sample_directory,
            forward_output=forward_out_path,
            reverse_output=reverse_out_path,
            remove_raw=True,
        )
