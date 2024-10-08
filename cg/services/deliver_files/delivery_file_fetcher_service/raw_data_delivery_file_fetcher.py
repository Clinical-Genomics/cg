import logging

from housekeeper.store.models import File

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import Workflow
from cg.services.deliver_files.delivery_file_fetcher_service.delivery_file_fetcher_service import (
    FetchDeliveryFilesService,
)
from cg.services.deliver_files.delivery_file_fetcher_service.error_handling import (
    handle_missing_bundle_errors,
)
from cg.services.deliver_files.delivery_file_fetcher_service.models import (
    DeliveryFiles,
    DeliveryMetaData,
    SampleFile,
)
from cg.services.deliver_files.delivery_file_tag_fetcher_service.bam_delivery_tags_fetcher import (
    BamDeliveryTagsFetcher,
)
from cg.services.deliver_files.delivery_file_tag_fetcher_service.sample_and_case_delivery_tags_fetcher import (
    SampleAndCaseDeliveryTagsFetcher,
)
from cg.store.models import Case
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class RawDataDeliveryFileFetcher(FetchDeliveryFilesService):
    """
    Fetch the raw data files for a case from Housekeeper.
    """

    def __init__(
        self,
        status_db: Store,
        hk_api: HousekeeperAPI,
        tags_fetcher: SampleAndCaseDeliveryTagsFetcher | BamDeliveryTagsFetcher,
    ):
        self.status_db = status_db
        self.hk_api = hk_api
        self.tags_fetcher = tags_fetcher

    def get_files_to_deliver(self, case_id: str) -> DeliveryFiles:
        """Return a list of raw data files to be delivered for a case and its samples."""
        LOG.debug(f"[FETCH SERVICE] Fetching raw data files for case: {case_id}")
        case: Case = self.status_db.get_case_by_internal_id(internal_id=case_id)
        sample_ids: list[str] = case.sample_ids
        raw_data_files: list[SampleFile] = []
        for sample_id in sample_ids:
            raw_data_files.extend(
                self._get_raw_data_files_for_sample(case_id=case_id, sample_id=sample_id)
            )
        delivery_data = DeliveryMetaData(
            customer_internal_id=case.customer.internal_id, ticket_id=case.latest_ticket
        )
        return DeliveryFiles(
            delivery_data=delivery_data,
            case_files=[],
            sample_files=raw_data_files,
        )

    @handle_missing_bundle_errors
    def _get_raw_data_files_for_sample(self, case_id: str, sample_id: str) -> list[SampleFile]:
        """Get the RawData files for a sample."""
        file_tags: list[set[str]] = self.tags_fetcher.fetch_tags(Workflow.RAW_DATA).sample_tags
        raw_data_files: list[File] = self.hk_api.get_files_from_latest_version_containing_tags(
            bundle_name=sample_id, tags=file_tags
        )
        sample_name: str = self.status_db.get_sample_by_internal_id(sample_id).name
        return [
            SampleFile(
                case_id=case_id,
                sample_id=sample_id,
                sample_name=sample_name,
                file_path=raw_data_file.full_path,
            )
            for raw_data_file in raw_data_files
        ]
