import logging
from pathlib import Path

from housekeeper.store.models import File

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import DataDelivery, Workflow
from cg.constants.delivery import PIPELINE_ANALYSIS_TAG_MAP
from cg.store.models import Case
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
        """Link files from Housekeeper bundle to customer's inbox."""
        raise NotImplementedError

    def get_files_to_deliver(self, case: Case) -> list[Path]:
        """Return a complete list of files to be delivered."""
        files_to_deliver: list[Path] = []
        if DataDelivery.FASTQ in case.data_delivery:
            fastq_sample_files: list[Path] = self.get_fastq_sample_files_to_deliver(case)
            files_to_deliver.extend(fastq_sample_files)
        if DataDelivery.ANALYSIS_FILES in case.data_delivery:
            analysis_case_files: list[Path] = self.get_analysis_case_files_to_deliver(case)
            analysis_sample_files: list[Path] = self.get_analysis_sample_files_to_deliver(case)
            files_to_deliver.extend(analysis_case_files + analysis_sample_files)
        return files_to_deliver

    def get_fastq_sample_files_to_deliver(self, case: Case) -> list[Path]:
        """Return a complete list of fastq sample files to be delivered."""
        raise NotImplementedError

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

    def get_analysis_sample_files_to_deliver(
        self, case: Case, sample_id: str | None = None
    ) -> list[Path]:
        """Return a list of sample files to be delivered, filtering by sample_id if provided."""
        sample_tags: list[set[str]] = self.get_analysis_sample_tags_for_workflow(case.data_analysis)
        if sample_tags and sample_id:
            for tag in sample_tags:
                tag.add(sample_id)
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
