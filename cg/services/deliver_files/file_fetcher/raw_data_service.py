import logging

from housekeeper.store.models import File

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import Workflow
from cg.services.deliver_files.file_fetcher.abstract import FetchDeliveryFilesService
from cg.services.deliver_files.file_fetcher.error_handling import handle_missing_bundle_errors
from cg.services.deliver_files.file_fetcher.exc import NoDeliveryFilesError
from cg.services.deliver_files.file_fetcher.models import (
    DeliveryFiles,
    DeliveryMetaData,
    SampleFile,
)
from cg.services.deliver_files.tag_fetcher.sample_and_case_service import (
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
        tags_fetcher: SampleAndCaseDeliveryTagsFetcher,
    ):
        self.status_db = status_db
        self.hk_api = hk_api
        self.tags_fetcher = tags_fetcher

    def get_files_to_deliver(self, case_id: str, sample_id: str | None = None) -> DeliveryFiles:
        """
        Return a list of raw data files to be delivered for a case and its samples.
        args:
            case_id: The case id to deliver files for
            sample_id: The sample id to deliver files for
        """
        LOG.debug(f"[FETCH SERVICE] Fetching raw data files for case: {case_id}")
        case: Case = self.status_db.get_case_by_internal_id(internal_id=case_id)
        sample_ids: list[str] = [sample_id] if sample_id else case.sample_ids
        raw_data_files: list[SampleFile] = []
        for sample_id in sample_ids:
            raw_data_files.extend(
                self._get_raw_data_files_for_sample(case_id=case_id, sample_id=sample_id)
            )
        delivery_data = DeliveryMetaData(
            case_id=case.internal_id,
            customer_internal_id=case.customer.internal_id,
            ticket_id=case.latest_ticket,
        )
        return self._validate_delivery_has_content(
            DeliveryFiles(
                delivery_data=delivery_data,
                case_files=[],
                sample_files=raw_data_files,
            )
        )

    @staticmethod
    def _validate_delivery_has_content(delivery_files: DeliveryFiles) -> DeliveryFiles:
        """Check if the delivery files has files to deliver.
        raises:
            NoDeliveryFilesError if no files to deliver.
        args:
            delivery_files: The delivery files to check
        """
        for sample_file in delivery_files.sample_files:
            LOG.debug(
                f"Found file to deliver: {sample_file.file_path} for sample: {sample_file.sample_id}"
            )
        if delivery_files.sample_files:
            return delivery_files
        LOG.info(
            f"No files to deliver for case {delivery_files.delivery_data.case_id} in ticket: {delivery_files.delivery_data.ticket_id}"
        )
        raise NoDeliveryFilesError

    @handle_missing_bundle_errors
    def _get_raw_data_files_for_sample(self, case_id: str, sample_id: str) -> list[SampleFile]:
        """
        Get the RawData files for a sample. Hardcoded tags to fetch from the raw data workflow.
        args:
            case_id: The case id to get the raw data files for
            sample_id: The sample id to get the raw data files for
        """
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
