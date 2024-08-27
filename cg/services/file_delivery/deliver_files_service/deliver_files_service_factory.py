"""Module for the factory of the deliver files service."""

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import Workflow
from cg.services.fastq_concatenation_service.fastq_concatenation_service import (
    FastqConcatenationService,
)
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
from cg.services.file_delivery.file_formatter_service.concatenation_delivery_file_formatter_service import (
    ConcatenationDeliveryFileFormatter,
)
from cg.services.file_delivery.file_formatter_service.delivery_file_formatting_service import (
    DeliveryFileFormattingService,
)
from cg.services.file_delivery.file_formatter_service.generic_delivery_file_formatter_service import (
    GenericDeliveryFileFormatter,
)
from cg.services.file_delivery.file_formatter_service.utils.sample_file_concatenation_formatter import (
    SampleFileConcatenationFormatter,
)
from cg.services.file_delivery.file_formatter_service.utils.sample_file_formatter import (
    SampleFileFormatter,
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


def get_deliver_file_formatter_service(workflow: Workflow) -> DeliveryFileFormattingService:
    """Get the file formatter service based on the workflow."""
    service_map = {
        Workflow.BALSAMIC: GenericDeliveryFileFormatter,
        Workflow.BALSAMIC_QC: GenericDeliveryFileFormatter,
        Workflow.BALSAMIC_UMI: GenericDeliveryFileFormatter,
        Workflow.MIP_DNA: GenericDeliveryFileFormatter,
        Workflow.MIP_RNA: GenericDeliveryFileFormatter,
        Workflow.FASTQ: GenericDeliveryFileFormatter,
        Workflow.RAREDISEASE: GenericDeliveryFileFormatter,
        Workflow.RNAFUSION: GenericDeliveryFileFormatter,
        Workflow.TAXPROFILER: GenericDeliveryFileFormatter,
        Workflow.TOMTE: GenericDeliveryFileFormatter,
        Workflow.MICROSALT: ConcatenationDeliveryFileFormatter,
        Workflow.MUTANT: ConcatenationDeliveryFileFormatter,
    }
    return service_map[workflow]


def get_sample_file_formatter_service(
    delivery_file_foramtter: DeliveryFileFormattingService,
) -> SampleFileFormatter | SampleFileConcatenationFormatter:
    """Get the sample file formatter service based on the delivery file formatter."""
    if isinstance(delivery_file_foramtter, GenericDeliveryFileFormatter):
        return SampleFileFormatter()
    concatenation_service = FastqConcatenationService()
    return SampleFileConcatenationFormatter(concatenation_service)
