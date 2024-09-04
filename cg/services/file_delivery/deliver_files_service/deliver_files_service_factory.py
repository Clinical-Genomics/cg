"""Module for the factory of the deliver files service."""

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.tb import TrailblazerAPI
from cg.constants import Workflow, DataDelivery
from cg.meta.rsync import RsyncAPI
from cg.services.fastq_concatenation_service.fastq_concatenation_service import (
    FastqConcatenationService,
)
from cg.services.file_delivery.deliver_files_service.deliver_files_service import (
    DeliverFilesService,
)
from cg.services.file_delivery.deliver_files_service.exc import DeliveryTypeNotSupported
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


class DeliveryServiceFactory:
    """Class to build the delivery services based on workflow and delivery type."""

    def __init__(
        self,
        store: Store,
        hk_api: HousekeeperAPI,
        rsync_service: RsyncAPI,
        tb_service: TrailblazerAPI,
    ):
        self.store = store
        self.hk_api = hk_api
        self.rsync_service = rsync_service
        self.tb_service = tb_service

    @staticmethod
    def _get_file_tag_fetcher(delivery_type: DataDelivery) -> FetchDeliveryFileTagsService:
        """Get the file tag fetcher based on the delivery type."""
        service_map: dict[DataDelivery, FetchDeliveryFileTagsService] = {
            DataDelivery.FASTQ: FetchSampleAndCaseDeliveryFileTagsService,
            DataDelivery.ANALYSIS_FILES: FetchSampleAndCaseDeliveryFileTagsService,
            DataDelivery.FASTQ_ANALYSIS: FetchSampleAndCaseDeliveryFileTagsService,
        }
        return service_map[delivery_type]()

    def _get_file_fetcher(self, delivery_type: DataDelivery) -> FetchDeliveryFilesService:
        """Get the file fetcher based on the delivery type."""
        service_map: dict[DataDelivery, FetchDeliveryFilesService] = {
            DataDelivery.FASTQ: FetchFastqDeliveryFilesService,
            DataDelivery.ANALYSIS_FILES: FetchAnalysisDeliveryFilesService,
            DataDelivery.FASTQ_ANALYSIS: FetchFastqAndAnalysisDeliveryFilesService,
        }
        file_tag_fetcher: FetchDeliveryFileTagsService = self._get_file_tag_fetcher(delivery_type)
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
        if workflow in [Workflow.MICROSALT]:
            return SampleFileConcatenationFormatter(FastqConcatenationService())
        return SampleFileFormatter()

    @staticmethod
    def _validate_delivery_type(delivery_type: DataDelivery):
        """Check if the delivery type is supported."""
        if delivery_type in [
            DataDelivery.FASTQ,
            DataDelivery.ANALYSIS_FILES,
            DataDelivery.FASTQ_ANALYSIS,
        ]:
            return
        raise DeliveryTypeNotSupported(
            f"Delivery type {delivery_type} is not supported. Supported delivery types are {DataDelivery.FASTQ}, {DataDelivery.ANALYSIS_FILES}, {DataDelivery.FASTQ_ANALYSIS}."
        )

    def build_delivery_service(
        self, workflow: Workflow, delivery_type: DataDelivery
    ) -> DeliverFilesService:
        """Build a delivery service based on the workflow and delivery type."""
        self._validate_delivery_type(delivery_type)
        file_fetcher: FetchDeliveryFilesService = self._get_file_fetcher(delivery_type)
        sample_file_formatter: SampleFileFormatter | SampleFileConcatenationFormatter = (
            self._get_sample_file_formatter(workflow)
        )
        file_formatter: DeliveryFileFormattingService = DeliveryFileFormatter(
            case_file_formatter=CaseFileFormatter(), sample_file_formatter=sample_file_formatter
        )
        return DeliverFilesService(
            delivery_file_manager_service=file_fetcher,
            move_file_service=MoveDeliveryFilesService(),
            file_formatter_service=file_formatter,
            status_db=self.store,
            rsync_service=self.rsync_service,
            tb_service=self.tb_service,
        )
