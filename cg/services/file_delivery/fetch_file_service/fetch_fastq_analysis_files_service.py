from cg.apps.housekeeper.hk import HousekeeperAPI
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
    def __init__(self, status_db: Store, hk_api: HousekeeperAPI):
        self.status_db = status_db
        self.hk_api = hk_api

    def get_files_to_deliver(self, case_id: str) -> DeliveryFiles:
        case: Case = self.status_db.get_case_by_internal_id(internal_id=case_id)
        fetch_fastq_service = FetchFastqDeliveryFilesService(
            self.status_db,
            self.hk_api,
            tags_fetcher=FetchSampleAndCaseDeliveryFileTagsService(),
        )
        fetch_analysis_service = FetchAnalysisDeliveryFilesService(
            self.status_db,
            self.hk_api,
            tags_fetcher=FetchSampleAndCaseDeliveryFileTagsService(),
        )
        fastq_files = fetch_fastq_service.get_files_to_deliver(case_id)
        analysis_files = fetch_analysis_service.get_files_to_deliver(case_id)
        delivery_data = DeliveryMetaData(
            customer_internal_id=case.customer.internal_id, ticket_id=case.latest_ticket
        )
        return DeliveryFiles(
            delivery_data=delivery_data,
            case_files=analysis_case_files,
            sample_files=analysis_sample_files,
        )
