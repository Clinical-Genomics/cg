import logging

from housekeeper.store.models import File

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import Workflow
from cg.services.deliver_files.file_fetcher.abstract import (
    FetchDeliveryFilesService,
)
from cg.services.deliver_files.file_fetcher.error_handling import (
    handle_missing_bundle_errors,
)
from cg.services.deliver_files.file_fetcher.exc import NoDeliveryFilesError
from cg.services.deliver_files.file_fetcher.models import (
    CaseFile,
    DeliveryFiles,
    DeliveryMetaData,
    SampleFile,
)
from cg.services.deliver_files.tag_fetcher.abstract import (
    FetchDeliveryFileTagsService,
)
from cg.store.models import Case
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class AnalysisDeliveryFileFetcher(FetchDeliveryFilesService):
    """
    Fetch the analysis files for a case from Housekeeper.
    """

    def __init__(
        self, status_db: Store, hk_api: HousekeeperAPI, tags_fetcher: FetchDeliveryFileTagsService
    ):
        self.status_db = status_db
        self.hk_api = hk_api
        self.tags_fetcher = tags_fetcher

    def get_files_to_deliver(self, case_id: str, sample_id: str | None = None) -> DeliveryFiles:
        """Return a list of analysis files to be delivered for a case.
        args:
            case_id: The case id to deliver files for
            sample_id: The sample id to deliver files for
        """
        LOG.debug(
            f"[FETCH SERVICE] Fetching analysis files for case: {case_id}, sample: {sample_id}"
        )
        case: Case = self.status_db.get_case_by_internal_id(internal_id=case_id)
        analysis_case_files: list[CaseFile] = self._get_analysis_case_delivery_files(
            case=case, sample_id=sample_id
        )

        analysis_sample_files: list[SampleFile] = self._get_analysis_sample_delivery_files(
            case=case, sample_id=sample_id
        )
        delivery_data = DeliveryMetaData(
            case_id=case.internal_id,
            customer_internal_id=case.customer.internal_id,
            ticket_id=case.latest_ticket,
        )

        return self._validate_delivery_has_content(
            DeliveryFiles(
                delivery_data=delivery_data,
                case_files=analysis_case_files,
                sample_files=analysis_sample_files,
            )
        )

    @staticmethod
    def _validate_delivery_has_content(delivery_files: DeliveryFiles) -> DeliveryFiles:
        """
        Check if the delivery files has files to deliver.
        raises:
            NoDeliveryFilesError if no files to deliver.
        args:
            delivery_files: The delivery files to check
        """
        if delivery_files.case_files or delivery_files.sample_files:
            return delivery_files
        LOG.info(
            f"No files to deliver for case {delivery_files.delivery_data.case_id} in ticket: {delivery_files.delivery_data.ticket_id}"
        )
        raise NoDeliveryFilesError

    @handle_missing_bundle_errors
    def _get_sample_files_from_case_bundle(
        self, workflow: Workflow, sample_id: str, case_id: str
    ) -> list[SampleFile] | None:
        """Return a list of files from a case bundle with a sample id as tag.
        This is to fetch sample specific analysis files that are stored on the case level.
        args:
            workflow: The workflow to fetch files for
            sample_id: The sample id to fetch files for
            case_id: The case id to fetch files for
        """
        sample_tags: list[set[str]] = self.tags_fetcher.fetch_tags(workflow).sample_tags
        if not sample_tags:
            return []
        sample_tags_with_sample_id: list[set[str]] = [tag | {sample_id} for tag in sample_tags]
        sample_files: list[File] = self.hk_api.get_files_from_latest_version_containing_tags(
            bundle_name=case_id, tags=sample_tags_with_sample_id
        )
        sample_name: str = self.status_db.get_sample_by_internal_id(sample_id).name
        return [
            SampleFile(
                case_id=case_id,
                sample_id=sample_id,
                sample_name=sample_name,
                file_path=sample_file.full_path,
            )
            for sample_file in sample_files
        ]

    def _get_analysis_sample_delivery_files(
        self, case: Case, sample_id: str | None
    ) -> list[SampleFile]:
        """Return all sample files to deliver for a case.
        Write a list of sample files to deliver for a case.
        args:
            case: The case to deliver files for
            sample_id: The sample id to deliver files for
        """
        sample_ids: list[str] = [sample_id] if sample_id else case.sample_ids
        delivery_files: list[SampleFile] = []
        for sample_id in sample_ids:
            sample_files: list[SampleFile] = self._get_sample_files_from_case_bundle(
                case_id=case.internal_id, sample_id=sample_id, workflow=case.data_analysis
            )
            delivery_files.extend(sample_files) if sample_files else None
        return delivery_files

    @handle_missing_bundle_errors
    def _get_analysis_case_delivery_files(
        self, case: Case, sample_id: str | None
    ) -> list[CaseFile]:
        """
        Return a complete list of analysis case files to be delivered and ignore analysis sample
        files. This is to ensure that only case level analysis files are delivered.
        args:
            case: The case to deliver files for
            sample_id: The sample id to deliver files for
        """
        case_tags: list[set[str]] = self.tags_fetcher.fetch_tags(case.data_analysis).case_tags
        if not case_tags:
            return []
        sample_id_tags: list[str] = [sample_id] if sample_id else case.sample_ids
        case_files: list[File] = self.hk_api.get_files_from_latest_version_containing_tags(
            bundle_name=case.internal_id, tags=case_tags, excluded_tags=sample_id_tags
        )
        return [
            CaseFile(
                case_id=case.internal_id,
                case_name=case.name,
                file_path=case_file.full_path,
            )
            for case_file in case_files
        ]
