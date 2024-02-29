"""Delivery API for handling file delivery to Caesar."""

import logging
from pathlib import Path

from housekeeper.store.models import File

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import DataDelivery, Workflow
from cg.constants.delivery import PIPELINE_ANALYSIS_TAG_MAP
from cg.store.models import Case, Sample
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class DeliveryAPI:
    """
    This class provides methods to handle the delivery process of files from the Housekeeper
    bundle to the customer's inbox.
    """

    def __init__(self, delivery_path: Path, housekeeper_api: HousekeeperAPI, store: Store):
        self.delivery_path = delivery_path
        self.housekeeper_api = housekeeper_api
        self.store = store

    def link_files_to_inbox(self) -> None:
        """Link files from Housekeeper bundle to the customer's inbox."""
        # TODO: dry-run
        # TODO: force flag
        # TODO: logging
        raise NotImplementedError

    def get_files_to_deliver(self, case: Case, force: bool) -> list[Path]:
        """Return a complete list of files to be delivered to the customer's inbox."""
        files_to_deliver: list[Path] = []
        if DataDelivery.FASTQ in case.data_delivery:
            fastq_files: list[Path] = self.get_fastq_files_to_deliver(case=case, force=force)
            files_to_deliver.extend(fastq_files)
        if DataDelivery.ANALYSIS_FILES in case.data_delivery:
            analysis_case_files: list[Path] = self.get_analysis_case_files_to_deliver(case)
            analysis_sample_files: list[Path] = self.get_analysis_sample_files_to_deliver(case=case)
            files_to_deliver.extend(analysis_case_files + analysis_sample_files)
        return files_to_deliver

    def get_fastq_files_to_deliver(self, case: Case, force: bool) -> list[Path]:
        """Return a complete list of fastq sample files to be delivered."""
        fastq_files: list[Path] = []
        for sample in case.samples:
            fastq_sample_files: list[Path] = self.get_fastq_files_to_deliver_by_sample(
                sample=sample, force=force
            )
            fastq_files.append(fastq_sample_files)
        return fastq_files

    def get_fastq_files_to_deliver_by_sample(self, sample: Sample, force: bool) -> list[Path]:
        """Return a list of fastq files to be delivered for a specific sample."""
        fastq_files: list[File] = []
        fastq_tags: list[set[str]] = self.get_analysis_sample_tags_for_workflow(Workflow.FASTQ)
        if self.is_sample_deliverable(sample=sample, force=force):
            fastq_files: list[File] = (
                self.housekeeper_api.get_files_from_latest_version_by_list_of_tags(
                    bundle_name=sample.internal_id, tags=fastq_tags
                )
            )
        return fastq_files

    def get_analysis_case_files_to_deliver(self, case: Case) -> list[Path]:
        """
        Return a complete list of analysis case files to be delivered and ignore analysis sample
        files.
        """
        case_tags: list[set[str]] = self.get_analysis_case_tags_for_workflow(case.data_analysis)
        sample_ids: list[set[str]] = [{sample_id} for sample_id in case.sample_ids]
        case_files: list[File] = self.housekeeper_api.get_files_from_latest_version_by_list_of_tags(
            bundle_name=case.internal_id, tags=case_tags, exclude_tags=sample_ids
        )
        return case_files

    def get_analysis_sample_files_to_deliver(self, case: Case) -> list[Path]:
        """Return a complete list of analysis sample files to be delivered."""
        sample_files: list[Path] = []
        for sample in case.samples:
            sample_files: list[Path] = self.get_analysis_sample_files_to_deliver_by_sample(
                case=case, sample=sample
            )
        return sample_files

    def get_analysis_sample_files_to_deliver_by_sample(
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
        return sample_files

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
