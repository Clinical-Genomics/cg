"""Module for the factory of the deliver files service."""

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import Workflow, DataDelivery
from cg.services.fastq_concatenation_service.fastq_concatenation_service import (
    FastqConcatenationService,
)
from cg.services.file_delivery.deliver_files_service.deliver_files_service import (
    DeliverFilesService,
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
from cg.services.file_delivery.file_formatter_service.delivery_file_formatter import (
    DeliveryFileFormatter,
)

from cg.services.file_delivery.file_formatter_service.delivery_file_formatting_service import (
    DeliveryFileFormattingService,
)
from cg.services.file_delivery.file_formatter_service.utils.case_file_formatter import (
    CaseFileFormatter,
)
from cg.services.file_delivery.file_formatter_service.utils.sample_file_concatenation_formatter import (
    SampleFileConcatenationFormatter,
)
from cg.services.file_delivery.file_formatter_service.utils.sample_file_formatter import (
    SampleFileFormatter,
)
from cg.services.file_delivery.move_files_service.move_delivery_files_service import (
    MoveDeliveryFilesService,
)
from cg.store.store import Store


class DeliveryServiceBuilder:
    """Class to build the delivery services based on workflow and delivery type."""

    def __init__(self, store: Store, hk_api: HousekeeperAPI):
        self.store = store
        self.hk_api = hk_api

    @staticmethod
    def _get_file_tag_fetcher(delivery_type: DataDelivery) -> FetchDeliveryFileTagsService:
        """Get the file tag fetcher based on the delivery type."""
        service_map = {
            DataDelivery.FASTQ: FetchSampleAndCaseDeliveryFileTagsService,
            DataDelivery.ANALYSIS_FILES: FetchSampleAndCaseDeliveryFileTagsService,
            DataDelivery.FASTQ_ANALYSIS: FetchSampleAndCaseDeliveryFileTagsService,
        }
        return service_map[delivery_type]()

    def _get_file_fetcher(self, delivery_type: DataDelivery) -> FetchDeliveryFilesService:
        """Get the file fetcher based on the delivery type."""
        service_map = {
            DataDelivery.FASTQ: FetchFastqDeliveryFilesService,
            DataDelivery.ANALYSIS_FILES: FetchAnalysisDeliveryFilesService,
            DataDelivery.FASTQ_ANALYSIS: FetchFastqAndAnalysisDeliveryFilesService,
        }
        file_tag_fetcher = self._get_file_tag_fetcher(delivery_type)
        return service_map[delivery_type](
            status_db=self.store,
            hk_api=self.hk_api,
            tags_fetcher=file_tag_fetcher,
        )

    @staticmethod
    def _get_sample_file_formatter(
        workflow: Workflow,
    ) -> SampleFileFormatter | SampleFileConcatenationFormatter:
        """Get the file formatter service based on the workflow."""
        if workflow in [Workflow.MICROSALT, Workflow.MUTANT]:
            return SampleFileConcatenationFormatter(FastqConcatenationService())
        return SampleFileFormatter()

    def build_delivery_service(
        self, workflow: Workflow, delivery_type: DataDelivery
    ) -> DeliverFilesService:
        """Build a delivery service based on the workflow and delivery type."""
        file_fetcher = self._get_file_fetcher(delivery_type)
        sample_file_formatter = self._get_sample_file_formatter(workflow)
        file_formatter: DeliveryFileFormattingService = DeliveryFileFormatter(
            case_file_formatter=CaseFileFormatter(), sample_file_formatter=sample_file_formatter
        )
        return DeliverFilesService(
            delivery_file_manager_service=file_fetcher,
            move_file_service=MoveDeliveryFilesService(),
            file_formatter_service=file_formatter,
            status_db=self.store,
        )
