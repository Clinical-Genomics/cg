"""Module for the factory of the deliver files service."""

from typing import Type

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.apps.tb import TrailblazerAPI
from cg.constants import DataDelivery, Workflow
from cg.constants.sequencing import SeqLibraryPrepCategory
from cg.services.analysis_service.analysis_service import AnalysisService
from cg.services.deliver_files.constants import DeliveryDestination, DeliveryStructure
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
from cg.services.deliver_files.file_formatter.destination.abstract import (
    DeliveryDestinationFormatter,
)
from cg.services.deliver_files.file_formatter.destination.base_service import BaseDeliveryFormatter
from cg.services.deliver_files.file_formatter.files.case_service import CaseFileFormatter
from cg.services.deliver_files.file_formatter.files.concatenation_service import (
    SampleFileConcatenationFormatter,
)
from cg.services.deliver_files.file_formatter.files.mutant_service import MutantFileFormatter
from cg.services.deliver_files.file_formatter.files.sample_service import (
    FileManager,
    SampleFileFormatter,
)
from cg.services.deliver_files.file_formatter.path_name.abstract import PathNameFormatter
from cg.services.deliver_files.file_formatter.path_name.flat_structure import (
    FlatStructurePathFormatter,
)
from cg.services.deliver_files.file_formatter.path_name.nested_structure import (
    NestedStructurePathFormatter,
)
from cg.services.deliver_files.file_mover.abstract import DestinationFilesMover
from cg.services.deliver_files.file_mover.base_service import BaseDestinationFilesMover
from cg.services.deliver_files.file_mover.customer_inbox_service import (
    CustomerInboxDestinationFilesMover,
)
from cg.services.deliver_files.rsync.service import DeliveryRsyncService
from cg.services.deliver_files.tag_fetcher.abstract import FetchDeliveryFileTagsService
from cg.services.deliver_files.tag_fetcher.fohm_upload_service import FOHMUploadTagsFetcher
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
    Class to build the delivery services based on case, workflow, delivery type, delivery
    destination and delivery structure.
    The delivery destination is used to specify delivery to the customer or for external upload.
    Workflow is used to specify the workflow of the case and is required for the tag fetcher.
    Delivery type is used to specify the type of delivery to perform.
    Delivery structure is used to specify the structure of the delivery.
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
        """Sanitise the delivery type.
        We have multiple delivery types that are a combination of other delivery types or uploads.
        Here we make sure to convert unsupported delivery types to supported ones.
        args:
            delivery_type: The type of delivery to perform.
        """
        if delivery_type in [DataDelivery.FASTQ_QC, DataDelivery.FASTQ_SCOUT]:
            return DataDelivery.FASTQ
        if delivery_type == DataDelivery.ANALYSIS_SCOUT:
            return DataDelivery.ANALYSIS_FILES
        if delivery_type in [
            DataDelivery.FASTQ_ANALYSIS_SCOUT,
            DataDelivery.FASTQ_QC_ANALYSIS,
        ]:
            return DataDelivery.FASTQ_ANALYSIS
        if delivery_type == DataDelivery.RAW_DATA_SCOUT:
            return DataDelivery.BAM
        if delivery_type == DataDelivery.RAW_DATA_ANALYSIS_SCOUT:
            return DataDelivery.RAW_DATA_ANALYSIS
        return delivery_type

    @staticmethod
    def _validate_delivery_type(delivery_type: DataDelivery) -> None:
        """
        Check if the delivery type is supported. Raises DeliveryTypeNotSupported error.
        args:
            delivery_type: The type of delivery to perform.
        Raises:
            DeliveryTypeNotSupported: If the delivery type is not supported.
        """
        if delivery_type not in [
            DataDelivery.ANALYSIS_FILES,
            DataDelivery.BAM,
            DataDelivery.FASTQ,
            DataDelivery.FASTQ_ANALYSIS,
            DataDelivery.RAW_DATA_ANALYSIS,
        ]:
            raise DeliveryTypeNotSupported(
                f"Delivery type {delivery_type} is not supported. Supported delivery types are"
                f" {DataDelivery.FASTQ}, {DataDelivery.ANALYSIS_FILES},"
                f" {DataDelivery.FASTQ_ANALYSIS}, {DataDelivery.BAM}, {DataDelivery.RAW_DATA_ANALYSIS}."
            )

    @staticmethod
    def _get_file_tag_fetcher(
        delivery_destination: DeliveryDestination,
    ) -> FetchDeliveryFileTagsService:
        """
        Return the correct file tag fetcher based on the delivery destination.
        NOTE: The FOHM upload requires a special tag system, all the other destination use
        sample and case tags.
        args:
            delivery_destination: The destination of the delivery defaults to customer.
        """
        if delivery_destination == DeliveryDestination.FOHM:
            return FOHMUploadTagsFetcher()
        return SampleAndCaseDeliveryTagsFetcher()

    def _get_file_fetcher(
        self, delivery_type: DataDelivery, delivery_destination: DeliveryDestination
    ) -> FetchDeliveryFilesService:
        """Get the file fetcher based on the delivery type.
        args:
            delivery_type: The type of delivery to perform.
            delivery_destination: The destination of the delivery defaults to customer. See DeliveryDestination enum for explanation.

        """
        service_map: dict[DataDelivery, Type[FetchDeliveryFilesService]] = {
            DataDelivery.FASTQ: RawDataDeliveryFileFetcher,
            DataDelivery.ANALYSIS_FILES: AnalysisDeliveryFileFetcher,
            DataDelivery.FASTQ_ANALYSIS: RawDataAndAnalysisDeliveryFileFetcher,
            DataDelivery.RAW_DATA_ANALYSIS: RawDataAndAnalysisDeliveryFileFetcher,
            DataDelivery.BAM: RawDataDeliveryFileFetcher,
        }
        file_tag_fetcher: FetchDeliveryFileTagsService = self._get_file_tag_fetcher(
            delivery_destination=delivery_destination
        )
        return service_map[delivery_type](
            status_db=self.store,
            hk_api=self.hk_api,
            tags_fetcher=file_tag_fetcher,
        )

    def _convert_workflow(self, case: Case) -> Workflow:
        """Change the workflow of a Microbial Fastq case to Microsalt to allow the concatenation of fastq files.
        With the introduction of the microbial-fastq delivery type, an unsupported combination of delivery type and
        workflow setup is required. This function makes sure that a raw data workflow with microbial fastq delivery
        type is treated as a microsalt workflow so that the microbial-fastq sample files can be concatenated.
        args:
            case: The case to convert the workflow for
        """
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
        delivery_structure: DeliveryStructure = DeliveryStructure.NESTED,
    ) -> SampleFileFormatter | SampleFileConcatenationFormatter | MutantFileFormatter:
        """Return the appropriate file formatter service based on the workflow.
        Depending on the delivery structure the path name formatter will be different.
        Args:
            case: The case to deliver files for.
            delivery_structure: The structure of the delivery. See DeliveryStructure enum for explanation. Defaults to nested.
        """

        converted_workflow: Workflow = self._convert_workflow(case)
        if converted_workflow in [Workflow.MICROSALT]:
            return SampleFileConcatenationFormatter(
                file_manager=FileManager(),
                path_name_formatter=self._get_path_name_formatter(delivery_structure),
                concatenation_service=FastqConcatenationService(),
            )
        if converted_workflow == Workflow.MUTANT:
            return MutantFileFormatter(
                lims_api=self.lims_api,
                file_manager=FileManager(),
                file_formatter=SampleFileConcatenationFormatter(
                    file_manager=FileManager(),
                    path_name_formatter=self._get_path_name_formatter(delivery_structure),
                    concatenation_service=FastqConcatenationService(),
                ),
            )
        return SampleFileFormatter(
            file_manager=FileManager(),
            path_name_formatter=self._get_path_name_formatter(delivery_structure),
        )

    def _get_case_file_formatter(self, delivery_structure: DeliveryStructure) -> CaseFileFormatter:
        """
        Get the case file formatter based on the delivery structure.
        args:
            delivery_structure: The structure of the delivery. See DeliveryStructure enum for explanation.
        """
        return CaseFileFormatter(
            file_manager=FileManager(),
            path_name_formatter=self._get_path_name_formatter(delivery_structure),
        )

    @staticmethod
    def _get_path_name_formatter(
        delivery_structure: DeliveryStructure,
    ) -> PathNameFormatter:
        """
        Get the path name formatter based on the delivery destination
        args:
            delivery_structure: The structure of the delivery. See DeliveryStructure enum for explanation.
        """
        if delivery_structure == DeliveryStructure.FLAT:
            return FlatStructurePathFormatter()
        return NestedStructurePathFormatter()

    @staticmethod
    def _get_file_mover(
        delivery_destination: DeliveryDestination,
    ) -> CustomerInboxDestinationFilesMover | BaseDestinationFilesMover:
        """Get the file mover based on the delivery type.
        args:
            delivery_destination: The destination of the delivery. See DeliveryDestination enum for explanation.
        """
        if delivery_destination in [DeliveryDestination.BASE, DeliveryDestination.FOHM]:
            return BaseDestinationFilesMover(FileMover(FileManager()))
        return CustomerInboxDestinationFilesMover(FileMover(FileManager()))

    def _get_file_formatter(
        self,
        delivery_structure: DeliveryStructure,
        case: Case,
    ) -> DeliveryDestinationFormatter:
        """
        Get the file formatter service based on the delivery destination.
        args:
            delivery_structure: The structure of the delivery. See DeliveryStructure enum for explanation.
            case: The case to deliver files for.
        """
        sample_file_formatter: (
            SampleFileFormatter | SampleFileConcatenationFormatter | MutantFileFormatter
        ) = self._get_sample_file_formatter(case=case, delivery_structure=delivery_structure)
        case_file_formatter: CaseFileFormatter = self._get_case_file_formatter(
            delivery_structure=delivery_structure
        )
        return BaseDeliveryFormatter(
            case_file_formatter=case_file_formatter,
            sample_file_formatter=sample_file_formatter,
        )

    def build_delivery_service(
        self,
        case: Case,
        delivery_type: DataDelivery | None = None,
        delivery_destination: DeliveryDestination = DeliveryDestination.CUSTOMER,
        delivery_structure: DeliveryStructure = DeliveryStructure.NESTED,
    ) -> DeliverFilesService:
        """Build a delivery service for a case.
        args:
            case: The case to deliver files for.
            delivery_type: The type of delivery to perform. See DataDelivery enum for explanation.
            delivery_destination: Representation of where the files will be uploaded.
                Defaults to 'customer'. See DeliveryDestination enum for explanation.
            delivery_structure: File structure for the delivery directory. Defaults to 'nested'.
                See DeliveryStructure enum for explanation.
        """
        delivery_type: DataDelivery = self._sanitise_delivery_type(
            delivery_type if delivery_type else case.data_delivery
        )
        self._validate_delivery_type(delivery_type)
        file_fetcher: FetchDeliveryFilesService = self._get_file_fetcher(
            delivery_type=delivery_type, delivery_destination=delivery_destination
        )
        file_move_service: DestinationFilesMover = self._get_file_mover(
            delivery_destination=delivery_destination
        )
        file_formatter: DeliveryDestinationFormatter = self._get_file_formatter(
            case=case, delivery_structure=delivery_structure
        )
        return DeliverFilesService(
            delivery_file_manager_service=file_fetcher,
            move_file_service=file_move_service,
            file_formatter_service=file_formatter,
            status_db=self.store,
            rsync_service=self.rsync_service,
            tb_service=self.tb_service,
            analysis_service=self.analysis_service,
        )
