"""Delivery API for handling file delivery to customer's inbox."""

import logging
from pathlib import Path

from housekeeper.store.models import File

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import DataDelivery, Workflow
from cg.constants.delivery import INBOX_NAME, PIPELINE_ANALYSIS_TAG_MAP
from cg.models.delivery.delivery import DeliveryFile
from cg.services.fastq_file_service.fastq_file_service import FastqFileService
from cg.store.models import Case, Sample
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class DeliveryAPI:
    """
    This class provides methods to handle the delivery process of files from the Housekeeper
    bundle to the customer's inbox.
    """

    def __init__(
        self,
        delivery_path: Path,
        fastq_file_service: FastqFileService,
        housekeeper_api: HousekeeperAPI,
        store: Store,
    ):
        self.delivery_path: Path = delivery_path
        self.fastq_file_service: FastqFileService = fastq_file_service
        self.housekeeper_api: HousekeeperAPI = housekeeper_api
        self.store: Store = store

    def link_delivery_files_to_inbox(self) -> None:
        """Link files from Housekeeper bundle to the customer's inbox."""
        # TODO: dry-run
        # TODO: force flag
        # TODO: logging
        raise NotImplementedError

    def get_delivery_files(self, case: Case, force: bool = False) -> list[DeliveryFile]:
        """Return a complete list of files to be delivered to the customer's inbox."""
        delivery_files: list[DeliveryFile] = []
        if DataDelivery.FASTQ in case.data_delivery:
            fastq_files: list[DeliveryFile] = self.get_fastq_delivery_files(case=case, force=force)
            delivery_files.extend(fastq_files)
        if DataDelivery.ANALYSIS_FILES in case.data_delivery:
            analysis_case_files: list[DeliveryFile] = self.get_analysis_case_delivery_files(case)
            analysis_sample_files: list[DeliveryFile] = self.get_analysis_sample_delivery_files(
                case=case
            )
            delivery_files.extend(analysis_case_files + analysis_sample_files)
        return delivery_files

    def get_fastq_delivery_files(self, case: Case, force: bool = False) -> list[DeliveryFile]:
        """Return a complete list of fastq sample files to be delivered."""
        delivery_files: list[DeliveryFile] = []
        for sample in case.samples:
            fastq_delivery_files: list[DeliveryFile] = self.get_fastq_delivery_files_by_sample(
                case=case, sample=sample, force=force
            )
            delivery_files.append(fastq_delivery_files)
        return delivery_files

    def get_fastq_delivery_files_by_sample(
        self, case: Case, sample: Sample, force: bool = False
    ) -> list[DeliveryFile]:
        """Return a list of fastq files to be delivered for a specific sample."""
        delivery_files: list[DeliveryFile] = []
        fastq_tags: list[set[str]] = self.get_analysis_sample_tags_for_workflow(Workflow.FASTQ)
        if self.is_sample_deliverable(sample=sample, force=force):
            fastq_files: list[File] = (
                self.housekeeper_api.get_files_from_latest_version_by_list_of_tags(
                    bundle_name=sample.internal_id, tags=fastq_tags
                )
            )
            delivery_files: list[DeliveryFile] = self.convert_files_to_delivery_files(
                files=fastq_files,
                case=case,
                source_id=sample.internal_id,
                destination_id=sample.name,
            )
        return delivery_files

    def get_analysis_case_delivery_files(self, case: Case) -> list[DeliveryFile]:
        """
        Return a complete list of analysis case files to be delivered and ignore analysis sample
        files.
        """
        case_tags: list[set[str]] = self.get_analysis_case_tags_for_workflow(case.data_analysis)
        sample_ids: list[set[str]] = [{sample_id} for sample_id in case.sample_ids]
        case_files: list[File] = self.housekeeper_api.get_files_from_latest_version_by_list_of_tags(
            bundle_name=case.internal_id, tags=case_tags, exclude_tags=sample_ids
        )
        delivery_files: list[DeliveryFile] = self.convert_files_to_delivery_files(
            files=case_files, case=case, source_id=case.internal_id, destination_id=case.name
        )
        return delivery_files

    def get_analysis_sample_delivery_files(self, case: Case) -> list[DeliveryFile]:
        """Return a complete list of analysis sample files to be delivered."""
        delivery_files: list[DeliveryFile] = []
        for sample in case.samples:
            sample_delivery_files: list[DeliveryFile] = (
                self.get_analysis_sample_delivery_files_by_sample(case=case, sample=sample)
            )
            delivery_files.append(sample_delivery_files)
        return delivery_files

    def get_analysis_sample_delivery_files_by_sample(
        self, case: Case, sample: Sample
    ) -> list[Path]:
        """Return a list of analysis files to be delivered for a specific sample."""
        sample_tags: list[set[str]] = self.get_analysis_sample_tags_for_workflow(case.data_analysis)
        for tag in sample_tags:
            tag.add(sample.internal_id)
        sample_files: list[File] = (
            self.housekeeper_api.get_files_from_latest_version_by_list_of_tags(
                bundle_name=case.internal_id, tags=sample_tags
            )
        )
        delivery_files: list[DeliveryFile] = self.convert_files_to_delivery_files(
            files=sample_files,
            case=case,
            source_id=sample.internal_id,
            destination_id=sample.name,
            analysis_sample_files=True,
        )
        return delivery_files

    def convert_files_to_delivery_files(
        self,
        files: list[File],
        case: Case,
        source_id: str,
        destination_id: str,
        analysis_sample_files: bool = False,
    ) -> list[DeliveryFile]:
        """Return a delivery file model given a list of housekeeper files."""
        delivery_files: list[DeliveryFile] = []
        destination_path: Path = Path(
            self.delivery_path, case.customer_id, INBOX_NAME, case.latest_ticket
        )
        if self.fastq_file_service.is_concatenation_needed(case):
            # TODO
            pass

        subfolder: Path = Path(destination_id)
        if analysis_sample_files:
            subfolder: Path = Path(case.name, destination_id)
        for file in files:
            destination_file_name: str = Path(file.full_path).name.replace(
                source_id, destination_id
            )
            destination_path: Path = Path(destination_path, subfolder, destination_file_name)
            delivery_file = DeliveryFile(
                source_path=Path(file.full_path), destination_path=destination_path
            )
            delivery_files.append(delivery_file)
        return delivery_files

    @staticmethod
    def get_analysis_case_tags_for_workflow(workflow: Workflow) -> list[set[str]]:
        return PIPELINE_ANALYSIS_TAG_MAP[workflow]["case_tags"]

    @staticmethod
    def get_analysis_sample_tags_for_workflow(workflow: Workflow) -> list[set[str]]:
        return PIPELINE_ANALYSIS_TAG_MAP[workflow]["sample_tags"]

    @staticmethod
    def is_sample_deliverable(sample: Sample, force: bool) -> bool:
        """Return whether the sample is deliverable or not."""
        is_external: bool = sample.application_version.application.is_external
        qc_pass: bool = sample.sequencing_qc
        return is_external or qc_pass or force
