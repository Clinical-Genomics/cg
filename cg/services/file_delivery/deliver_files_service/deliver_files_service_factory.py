"""Module for the factory of the deliver files service."""

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import Workflow
from cg.services.file_delivery.fetch_delivery_files_tags.fetch_delivery_file_tags_service import (
    FetchDeliveryFileTagsService,
)
from cg.services.file_delivery.fetch_delivery_files_tags.fetch_sample_and_case_delivery_file_tags_service import (
    FetchSampleAndCaseDeliveryFileTagsService,
)
from cg.services.file_delivery.fetch_file_service.fetch_analysis_files_service import (
    FetchAnalysisDeliveryFilesService,
)
from cg.services.file_delivery.fetch_file_service.fetch_delivery_files_service import (
    FetchDeliveryFilesService,
)
from cg.services.file_delivery.fetch_file_service.fetch_fastq_analysis_files_service import (
    FetchFastqAndAnalysisDeliveryFilesService,
)
from cg.services.file_delivery.fetch_file_service.fetch_fastq_files_service import (
    FetchFastqDeliveryFilesService,
)
from cg.services.file_delivery.file_formatter_service.delivery_file_formatting_service import (
    DeliveryFileFormattingService,
)
from cg.store.store import Store


def get_file_tag_fetcher(delivery_type: str) -> FetchDeliveryFileTagsService:
    """Get the file tag fetcher based on the delivery type."""
    service_map = {
        "fastq": FetchSampleAndCaseDeliveryFileTagsService,
        "analysis": FetchSampleAndCaseDeliveryFileTagsService,
        "analysis_fastq": FetchSampleAndCaseDeliveryFileTagsService,
    }
    return service_map[delivery_type]


def get_fetch_file_service(delivery_type: str) -> FetchDeliveryFilesService:
    """Get the file tag fetcher based on the delivery type."""
    service_map = {
        "fastq": FetchFastqDeliveryFilesService,
        "analysis": FetchAnalysisDeliveryFilesService,
        "analysis_fastq": FetchFastqAndAnalysisDeliveryFilesService,
    }
    return service_map[delivery_type]


def get_file_formatter_service(workflow: Workflow) -> DeliveryFileFormattingService:
    """Get the file formatter service based on the workflow."""
    service_map = {}
    return service_map[workflow]
