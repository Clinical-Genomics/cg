from cg.apps.housekeeper.hk import HousekeeperAPI
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
from cg.services.file_delivery.fetch_file_service.fetch_fastq_files_service import (
    FetchFastqDeliveryFilesService,
)
from cg.services.file_delivery.fetch_file_service.models import DeliveryFiles, DeliveryMetaData
from cg.store.models import Case
from cg.store.store import Store


class FetchFastqAndAnalysisDeliveryFilesService(FetchDeliveryFilesService):

    def __init__(
        self, status_db: Store, hk_api: HousekeeperAPI, tags_fetcher: FetchDeliveryFileTagsService
    ):
        self.status_db = status_db
        self.hk_api = hk_api
        self.tags_fetcher = tags_fetcher

    def get_files_to_deliver(self, case_id: str) -> DeliveryFiles:
        case = self._get_case(case_id)
        fastq_files = self._fetch_files(FetchFastqDeliveryFilesService, case_id)
        analysis_files = self._fetch_files(FetchAnalysisDeliveryFilesService, case_id)
        delivery_data = DeliveryMetaData(
            customer_internal_id=case.customer.internal_id, ticket_id=case.latest_ticket
        )

        return DeliveryFiles(
            delivery_data=delivery_data,
            case_files=analysis_files.case_files,
            sample_files=analysis_files.sample_files + fastq_files.sample_files,
        )

    def _get_case(self, case_id: str) -> Case:
        """Fetch the case from the database."""
        return self.status_db.get_case_by_internal_id(internal_id=case_id)

    def _fetch_files(self, service_class: type, case_id: str) -> DeliveryFiles:
        """Fetch files using the provided service class."""
        service = service_class(self.status_db, self.hk_api, tags_fetcher=self.tags_fetcher)
        return service.get_files_to_deliver(case_id)
