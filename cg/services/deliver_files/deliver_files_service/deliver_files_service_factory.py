"""Module for the factory of the deliver files service."""

from typing import Type

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.apps.tb import TrailblazerAPI
from cg.constants import DataDelivery, Workflow
from cg.constants.sequencing import SeqLibraryPrepCategory
from cg.services.analysis_service.analysis_service import AnalysisService
from cg.services.deliver_files.constants import DeliveryDestination
from cg.services.deliver_files.deliver_files_service.deliver_files_service import (
    DeliverFilesService,
)
from cg.services.deliver_files.deliver_files_service.exc import DeliveryTypeNotSupported
from cg.services.deliver_files.file_fetcher.abstract import FetchDeliveryFilesService
from cg.services.deliver_files.file_fetcher.analysis_raw_data_service import (
    RawDataAndAnalysisDeliveryFileFetcher,
)
from cg.services.deliver_files.file_fetcher.analysis_service import AnalysisDeliveryFileFetcher
from cg.services.deliver_files.file_fetcher.raw_data_service import RawDataDeliveryFileFetcher
from cg.services.deliver_files.file_filter.sample_service import SampleFileFilter
from cg.services.deliver_files.file_formatter.destination.abstract import (
    DeliveryDestinationFormatter,
)
from cg.services.deliver_files.file_formatter.destination.customer_inbox_service import (
    CustomerInboxDeliveryFormatter,
)
from cg.services.deliver_files.file_formatter.destination.base_service import (
    BaseDeliveryFormatter,
)
from cg.services.deliver_files.file_formatter.component_file.case_service import CaseFileFormatter
from cg.services.deliver_files.file_formatter.component_file.mutant_service import (
    MutantFileFormatter,
)
from cg.services.deliver_files.file_formatter.component_file.concatenation_service import (
    SampleFileConcatenationFormatter,
)
from cg.services.deliver_files.file_formatter.component_file.sample_service import (
    SampleFileFormatter,
    FileManager,
)
from cg.services.deliver_files.file_formatter.path_name.flat_structure import (
    FlatStructurePathFormatter,
)
from cg.services.deliver_files.file_formatter.path_name.nested_structure import (
    NestedStructurePathFormatter,
)
from cg.services.deliver_files.file_mover.delivery_files_mover import CustomerInboxFilesMover
from cg.services.deliver_files.file_mover.fohm_upload_files_mover import BaseFilesMover
from cg.services.deliver_files.rsync.service import DeliveryRsyncService
from cg.services.deliver_files.tag_fetcher.abstract import FetchDeliveryFileTagsService
from cg.services.deliver_files.tag_fetcher.bam_service import BamDeliveryTagsFetcher
from cg.services.deliver_files.tag_fetcher.sample_and_case_service import (
    SampleAndCaseDeliveryTagsFetcher,
)
from cg.services.deliver_files.utils import FileMover
from cg.services.fastq_concatenation_service.fastq_concatenation_service import (
    FastqConcatenationService,
)
from cg.store.models import Case
from cg.store.store import Store


class DeliveryServiceFactory:
    """
    Class to build the delivery services based on workflow, delivery type, delivery destination.
    The delivery destination is used to specify delivery to the customer or for upload.
    It determines how the delivery_base_path is managed and its underlying folder structure.
    """

    def __init__(
        self,
        store: Store,
        lims_api: LimsAPI,
        hk_api: HousekeeperAPI,
        rsync_service: DeliveryRsyncService,
        tb_service: TrailblazerAPI,
        analysis_service: AnalysisService,
    ):
        self.store = store
        self.lims_api = lims_api
        self.hk_api = hk_api
        self.rsync_service = rsync_service
        self.tb_service = tb_service
        self.analysis_service = analysis_service

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
            f"Delivery type {delivery_type} is not supported. Supported delivery types are"
            f" {DataDelivery.FASTQ}, {DataDelivery.ANALYSIS_FILES},"
            f" {DataDelivery.FASTQ_ANALYSIS}, {DataDelivery.BAM}."
        )

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

    def _convert_workflow(self, case: Case) -> Workflow:
        """Converts a workflow with the introduction of the microbial-fastq delivery type an
        unsupported combination of delivery type and workflow setup is required. This function
        makes sure that a raw data workflow with microbial fastq delivery type is treated as a
        microsalt workflow so that the microbial-fastq sample files can be concatenated."""
        tag: str = case.samples[0].application_version.application.tag
        microbial_tags: list[str] = [
            application.tag
            for application in self.store.get_active_applications_by_prep_category(
                prep_category=SeqLibraryPrepCategory.MICROBIAL
            )
        ]
        if case.data_analysis == Workflow.RAW_DATA and tag in microbial_tags:
            return Workflow.MICROSALT
        return case.data_analysis

    def _get_sample_file_formatter(
        self,
        case: Case,
        delivery_destination: DeliveryDestination,
    ) -> SampleFileFormatter | SampleFileConcatenationFormatter | MutantFileFormatter:
        """Get the file formatter service based on the workflow."""
        converted_workflow: Workflow = self._convert_workflow(case)
        if converted_workflow in [Workflow.MICROSALT]:
            return SampleFileConcatenationFormatter(
                file_manager=FileManager(),
                file_formatter=NestedStructurePathFormatter(),
                concatenation_service=FastqConcatenationService(),
            )
        if converted_workflow == Workflow.MUTANT:
            if delivery_destination == DeliveryDestination.BASE:
                return MutantFileFormatter(
                    lims_api=self.lims_api,
                    file_manager=FileManager(),
                    file_formatter=SampleFileConcatenationFormatter(
                        file_manager=FileManager(),
                        file_formatter=FlatStructurePathFormatter(),
                        concatenation_service=FastqConcatenationService(),
                    ),
                )
            return MutantFileFormatter(
                lims_api=self.lims_api,
                file_manager=FileManager(),
                file_formatter=SampleFileConcatenationFormatter(
                    file_manager=FileManager(),
                    file_formatter=NestedStructurePathFormatter(),
                    concatenation_service=FastqConcatenationService(),
                ),
            )
        return SampleFileFormatter(
            file_manager=FileManager(), file_name_formatter=NestedStructurePathFormatter()
        )

    @staticmethod
    def _get_file_mover(
        delivery_destination: DeliveryDestination,
    ) -> CustomerInboxFilesMover | BaseFilesMover:
        """Get the file mover based on the delivery type.
        Args:
            delivery_destination: The destination of the delivery defaults to customer.
        """
        if delivery_destination == DeliveryDestination.BASE:
            return BaseFilesMover(FileMover(FileManager()))
        return CustomerInboxFilesMover(FileMover(FileManager()))

    def _get_file_formatter(
        self,
        delivery_destination: DeliveryDestination,
        case: Case,
    ) -> DeliveryDestinationFormatter:
        """Get the file formatter service based on the delivery destination."""
        sample_file_formatter: (
            SampleFileFormatter | SampleFileConcatenationFormatter | MutantFileFormatter
        ) = self._get_sample_file_formatter(case=case, delivery_destination=delivery_destination)
        if delivery_destination == DeliveryDestination.BASE:
            return BaseDeliveryFormatter(
                case_file_formatter=CaseFileFormatter(),
                sample_file_formatter=sample_file_formatter,
            )
        return CustomerInboxDeliveryFormatter(
            case_file_formatter=CaseFileFormatter(
                file_manager=FileManager(), path_name_formatter=NestedStructurePathFormatter()
            ),
            sample_file_formatter=sample_file_formatter,
        )

    def build_delivery_service(
        self,
        case: Case,
        delivery_type: DataDelivery | None = None,
        delivery_destination: DeliveryDestination = DeliveryDestination.CUSTOMER,
    ) -> DeliverFilesService:
        """Build a delivery service based on a case.

        Args:
            case: The case to deliver files for.
            delivery_type: The type of delivery to perform.
            delivery_destination: The destination of the delivery defaults to customer.
        """
        delivery_type: DataDelivery = self._sanitise_delivery_type(
            delivery_type if delivery_type else case.data_delivery
        )
        self._validate_delivery_type(delivery_type)
        file_fetcher: FetchDeliveryFilesService = self._get_file_fetcher(delivery_type)
        file_move_service: CustomerInboxFilesMover | BaseFilesMover = self._get_file_mover(
            delivery_destination=delivery_destination
        )
        file_formatter: DeliveryDestinationFormatter = self._get_file_formatter(
            case=case, delivery_destination=delivery_destination
        )
        return DeliverFilesService(
            delivery_file_manager_service=file_fetcher,
            move_file_service=file_move_service,
            file_filter=SampleFileFilter(),
            file_formatter_service=file_formatter,
            status_db=self.store,
            rsync_service=self.rsync_service,
            tb_service=self.tb_service,
            analysis_service=self.analysis_service,
        )
