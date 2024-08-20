from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.services.file_delivery.fetch_delivery_files_tags.fetch_analysis_delivery_file_tags_service import (
    FetchAnalysisDeliveryFileTagsService,
)
from cg.services.file_delivery.fetch_delivery_files_tags.fetch_fastq_delivery_file_tags_service import (
    FetchFastqDeliveryFileTagsService,
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
from cg.services.file_delivery.fetch_file_service.models import DeliveryFiles
from cg.store.store import Store


class FetchFastqAndAnalysisDeliveryFilesService(FetchDeliveryFilesService):
    def __init__(self, status_db: Store, hk_api: HousekeeperAPI):
        self.status_db = status_db
        self.hk_api = hk_api

    def get_files_to_deliver(self, case_id: str) -> DeliveryFiles:
        fetch_fastq_service = FetchFastqDeliveryFilesService(
            self.status_db,
            self.hk_api,
            tags_fetcher=FetchFastqDeliveryFileTagsService(),
        )
        fetch_analysis_service = FetchAnalysisDeliveryFilesService(
            self.status_db,
            self.hk_api,
            tags_fetcher=FetchAnalysisDeliveryFileTagsService(),
        )
        fastq_files = fetch_fastq_service.get_files_to_deliver(case_id)
        analysis_files = fetch_analysis_service.get_files_to_deliver(case_id)
        return DeliveryFiles(
            case_files=analysis_files.case_files,
            sample_files=fastq_files.sample_files + analysis_files.sample_files,
        )
