"""Delivery API for handling file delivery to customer's inbox."""

import logging
from pathlib import Path

from housekeeper.store.models import File

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import DataDelivery, Workflow
from cg.constants.delivery import INBOX_NAME, PIPELINE_ANALYSIS_TAG_MAP
from cg.models.delivery.delivery import DeliveryFile
from cg.services.fastq_concatenation_service.fastq_concatenation_service import (
    FastqConcatenationService,
)
from cg.services.sequencing_qc_service.sequencing_qc_service import SequencingQCService
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
        fastq_concatenation_service: FastqConcatenationService,
        housekeeper_api: HousekeeperAPI,
        store: Store,
    ):
        self.delivery_path: Path = delivery_path
        self.fastq_file_service: FastqConcatenationService = fastq_concatenation_service
        self.housekeeper_api: HousekeeperAPI = housekeeper_api
        self.store: Store = store

    def get_analysis_sample_delivery_files_by_sample(
        self, case: Case, sample: Sample
    ) -> list[DeliveryFile]:
        """Return a list of analysis files to be delivered for a specific sample."""
        sample_tags: list[set[str]] = self.get_analysis_sample_tags_for_workflow(case.data_analysis)
        sample_tags_with_sample_id: list[set[str]] = [
            tag | {sample.internal_id} for tag in sample_tags
        ]
        sample_files: list[File] = (
            self.housekeeper_api.get_files_from_latest_version_containing_tags(
                bundle_name=case.internal_id, tags=sample_tags_with_sample_id
            )
        )
        delivery_files: list[DeliveryFile] = self.convert_files_to_delivery_files(
            files=sample_files,
            case=case,
            internal_id=sample.internal_id,
            external_id=sample.name,
            analysis_sample_files=True,
        )
        return delivery_files

    def get_analysis_sample_delivery_files(self, case: Case) -> list[DeliveryFile]:
        """Return a complete list of analysis sample files to be delivered."""
        delivery_files: list[DeliveryFile] = []
        for sample in case.samples:
            sample_delivery_files: list[DeliveryFile] = (
                self.get_analysis_sample_delivery_files_by_sample(case=case, sample=sample)
            )
            delivery_files.extend(sample_delivery_files)
        return delivery_files

    def get_analysis_case_delivery_files(self, case: Case) -> list[DeliveryFile]:
        """
        Return a complete list of analysis case files to be delivered and ignore analysis sample
        files.
        """
        case_tags: list[set[str]] = self.get_analysis_case_tags_for_workflow(case.data_analysis)
        sample_id_tags: list[str] = [sample_id for sample_id in case.sample_ids]
        case_files: list[File] = self.housekeeper_api.get_files_from_latest_version_containing_tags(
            bundle_name=case.internal_id, tags=case_tags, excluded_tags=sample_id_tags
        )
        delivery_files: list[DeliveryFile] = self.convert_files_to_delivery_files(
            files=case_files, case=case, internal_id=case.internal_id, external_id=case.name
        )
        return delivery_files

    def get_delivery_files(self, case: Case, force: bool = False) -> list[DeliveryFile]:
        """Return a complete list of files to be delivered to the customer's inbox."""
        delivery_files: list[DeliveryFile] = []

        analysis_case_files: list[DeliveryFile] = self.get_analysis_case_delivery_files(case)
        analysis_sample_files: list[DeliveryFile] = self.get_analysis_sample_delivery_files(
            case=case
        )
        delivery_files.extend(analysis_case_files + analysis_sample_files)
        return delivery_files
