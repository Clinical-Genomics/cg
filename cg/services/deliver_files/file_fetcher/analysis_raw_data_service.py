from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.services.deliver_files.file_fetcher.analysis_service import (
    AnalysisDeliveryFileFetcher,
)
from cg.services.deliver_files.file_fetcher.abstract import (
    FetchDeliveryFilesService,
)
from cg.services.deliver_files.file_fetcher.models import (
    DeliveryFiles,
    DeliveryMetaData,
)
from cg.services.deliver_files.file_fetcher.raw_data_service import (
    RawDataDeliveryFileFetcher,
)
from cg.services.deliver_files.tag_fetcher.abstract import (
    FetchDeliveryFileTagsService,
)
from cg.store.models import Case
from cg.store.store import Store


class RawDataAndAnalysisDeliveryFileFetcher(FetchDeliveryFilesService):

    def __init__(
        self, status_db: Store, hk_api: HousekeeperAPI, tags_fetcher: FetchDeliveryFileTagsService
    ):
        self.status_db = status_db
        self.hk_api = hk_api
        self.tags_fetcher = tags_fetcher

    def get_files_to_deliver(self, case_id: str, sample_id: str | None = None) -> DeliveryFiles:
        """
        Get files to deliver for a case or sample for both analysis and raw data.
        args:
            case_id: The case id to deliver files for
            sample_id: The sample id to deliver files for
        """
        case: Case = self.status_db.get_case_by_internal_id(internal_id=case_id)
        fastq_files: DeliveryFiles = self._fetch_files(
            service_class=RawDataDeliveryFileFetcher, case_id=case_id, sample_id=sample_id
        )
        analysis_files: DeliveryFiles = self._fetch_files(
            service_class=AnalysisDeliveryFileFetcher, case_id=case_id, sample_id=sample_id
        )
        delivery_data = DeliveryMetaData(
            case_id=case.internal_id,
            customer_internal_id=case.customer.internal_id,
            ticket_id=case.latest_ticket,
        )

        return DeliveryFiles(
            delivery_data=delivery_data,
            case_files=analysis_files.case_files,
            sample_files=analysis_files.sample_files + fastq_files.sample_files,
        )

    def _fetch_files(
        self, service_class: type, case_id: str, sample_id: str | None
    ) -> DeliveryFiles:
        """Fetch files using the provided service class.
        Wrapper to fetch files using the provided service class. This is either the RawDataDeliveryFileFetcher or the AnalysisDeliveryFileFetcher.
        args:
            service_class: The service class to use to fetch the files
            case_id: The case id to fetch files for
            sample_id: The sample id to fetch files for
        """
        service = service_class(self.status_db, self.hk_api, tags_fetcher=self.tags_fetcher)
        return service.get_files_to_deliver(case_id=case_id, sample_id=sample_id)
