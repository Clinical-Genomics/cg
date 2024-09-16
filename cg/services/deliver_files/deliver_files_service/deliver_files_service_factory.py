"""Module for the factory of the deliver files service."""

from typing import Type
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.tb import TrailblazerAPI
from cg.constants import Workflow, DataDelivery
from cg.services.analysis_service.analysis_service import AnalysisService
from cg.services.deliver_files.delivery_file_tag_fetcher_service.bam_delivery_tags_fetcher import (
    BamDeliveryTagsFetcher,
)
from cg.services.fastq_concatenation_service.fastq_concatenation_service import (
    FastqConcatenationService,
)
from cg.services.deliver_files.deliver_files_service.deliver_files_service import (
    DeliverFilesService,
)
from cg.services.deliver_files.deliver_files_service.exc import DeliveryTypeNotSupported
from cg.services.deliver_files.delivery_file_tag_fetcher_service.delivery_file_tag_fetcher_service import (
    FetchDeliveryFileTagsService,
)
from cg.services.deliver_files.delivery_file_tag_fetcher_service.sample_and_case_delivery_tags_fetcher import (
    SampleAndCaseDeliveryTagsFetcher,
)
from cg.services.deliver_files.delivery_file_fetcher_service.analysis_delivery_file_fetcher import (
    AnalysisDeliveryFileFetcher,
)
from cg.services.deliver_files.delivery_file_fetcher_service.delivery_file_fetcher_service import (
    FetchDeliveryFilesService,
)
from cg.services.deliver_files.delivery_file_fetcher_service.raw_data_and_analysis_delivery_file_fetcher import (
    RawDataAndAnalysisDeliveryFileFetcher,
)
from cg.services.deliver_files.delivery_file_fetcher_service.raw_data_delivery_file_fetcher import (
    RawDataDeliveryFileFetcher,
)
from cg.services.deliver_files.delivery_file_formatter_service.delivery_file_formatter import (
    DeliveryFileFormatter,
)

from cg.services.deliver_files.delivery_file_formatter_service.delivery_file_formatting_service import (
    DeliveryFileFormattingService,
)
from cg.services.deliver_files.delivery_file_formatter_service.utils.case_file_formatter import (
    CaseFileFormatter,
)
from cg.services.deliver_files.delivery_file_formatter_service.utils.sample_file_concatenation_formatter import (
    SampleFileConcatenationFormatter,
)
from cg.services.deliver_files.delivery_file_formatter_service.utils.sample_file_formatter import (
    SampleFileFormatter,
)
from cg.services.deliver_files.delivery_file_mover_service.delivery_file_mover import (
    DeliveryFilesMover,
)
from cg.services.deliver_files.delivery_rsync_service.delivery_rsync_service import (
    DeliveryRsyncService,
)
from cg.store.store import Store


class DeliveryServiceFactory:
    """Class to build the delivery services based on workflow and delivery type."""

    def __init__(
        self,
        store: Store,
        hk_api: HousekeeperAPI,
        rsync_service: DeliveryRsyncService,
        tb_service: TrailblazerAPI,
        analysis_service: AnalysisService,
    ):
        self.store = store
        self.hk_api = hk_api
        self.rsync_service = rsync_service
        self.tb_service = tb_service
        self.analysis_service = analysis_service

    @staticmethod
    def _get_file_tag_fetcher(delivery_type: DataDelivery) -> FetchDeliveryFileTagsService:
        """Get the file tag fetcher based on the delivery type."""
        service_map: dict[DataDelivery, Type[FetchDeliveryFileTagsService]] = {
            DataDelivery.FASTQ: SampleAndCaseDeliveryTagsFetcher,
            DataDelivery.ANALYSIS_FILES: SampleAndCaseDeliveryTagsFetcher,
            DataDelivery.FASTQ_ANALYSIS: SampleAndCaseDeliveryTagsFetcher,
            DataDelivery.BAM: BamDeliveryTagsFetcher,
        }
        return service_map[delivery_type]()

    def _get_file_fetcher(self, delivery_type: DataDelivery) -> FetchDeliveryFilesService:
        """Get the file fetcher based on the delivery type."""
        service_map: dict[DataDelivery, Type[FetchDeliveryFilesService]] = {
            DataDelivery.FASTQ: RawDataDeliveryFileFetcher,
            DataDelivery.ANALYSIS_FILES: AnalysisDeliveryFileFetcher,
            DataDelivery.FASTQ_ANALYSIS: RawDataAndAnalysisDeliveryFileFetcher,
            DataDelivery.BAM: RawDataDeliveryFileFetcher,
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
        """Check if the delivery type is supported. Raises DeliveryTypeNotSupported error."""
        if delivery_type in [
            DataDelivery.FASTQ,
            DataDelivery.ANALYSIS_FILES,
            DataDelivery.FASTQ_ANALYSIS,
            DataDelivery.BAM,
        ]:
            return
        raise DeliveryTypeNotSupported(
            f"Delivery type {delivery_type} is not supported. Supported delivery types are {DataDelivery.FASTQ}, {DataDelivery.ANALYSIS_FILES}, {DataDelivery.FASTQ_ANALYSIS}, {DataDelivery.BAM}."
        )

    def build_delivery_service(
        self, workflow: Workflow, delivery_type: DataDelivery
    ) -> DeliverFilesService:
        """Build a delivery service based on the workflow and delivery type."""
        delivery_type: DataDelivery = self._sanitise_delivery_type(delivery_type)
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
            move_file_service=DeliveryFilesMover(),
            file_formatter_service=file_formatter,
            status_db=self.store,
            rsync_service=self.rsync_service,
            tb_service=self.tb_service,
            analysis_service=self.analysis_service,
        )

    @staticmethod
    def _sanitise_delivery_type(delivery_type: DataDelivery) -> DataDelivery:
        """Sanitise the delivery type."""
        if delivery_type in [DataDelivery.FASTQ_QC, DataDelivery.FASTQ_SCOUT]:
            return DataDelivery.FASTQ
        if delivery_type in [DataDelivery.ANALYSIS_SCOUT]:
            return DataDelivery.ANALYSIS_FILES
        if delivery_type in [
            DataDelivery.FASTQ_ANALYSIS_SCOUT,
            DataDelivery.FASTQ_QC_ANALYSIS,
        ]:
            return DataDelivery.FASTQ_ANALYSIS
        return delivery_type
