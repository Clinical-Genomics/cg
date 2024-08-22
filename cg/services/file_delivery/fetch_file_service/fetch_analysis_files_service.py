from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import Workflow
from cg.services.file_delivery.fetch_delivery_files_tags.fetch_delivery_file_tags_service import (
    FetchDeliveryFileTagsService,
)
from cg.services.file_delivery.fetch_file_service.fetch_delivery_files_service import (
    FetchDeliveryFilesService,
)
from housekeeper.store.models import File

from cg.services.file_delivery.fetch_file_service.models import (
    SampleFile,
    CaseFile,
    DeliveryFiles,
    DeliveryMetaData,
)
from cg.store.models import Case

from cg.store.store import Store


class FetchAnalysisDeliveryFilesService(FetchDeliveryFilesService):
    """
    Fetch the analysis files for a case from Housekeeper.
    """

    def __init__(
        self, status_db: Store, hk_api: HousekeeperAPI, tags_fetcher: FetchDeliveryFileTagsService
    ):
        self.status_db = status_db
        self.hk_api = hk_api
        self.tags_fetcher = tags_fetcher

    def get_files_to_deliver(self, case_id: str) -> DeliveryFiles:
        """Return a list of analysis files to be delivered for a case."""
        case: Case = self.status_db.get_case_by_internal_id(internal_id=case_id)
        analysis_case_files: list[CaseFile] = self.get_analysis_case_delivery_files(case)
        analysis_sample_files: list[SampleFile] = self._get_analysis_sample_delivery_files(case)
        delivery_data = DeliveryMetaData(
            customer_internal_id=case.customer.internal_id, ticket_id=case.latest_ticket
        )
        return DeliveryFiles(
            delivery_data=delivery_data,
            case_files=analysis_case_files,
            sample_files=analysis_sample_files,
        )

    def _get_sample_files_from_case_bundle(
        self, workflow: Workflow, sample_id: str, case_id: str
    ) -> list[SampleFile]:
        """Return a list of files from a case bundle with a sample id as tag."""
        sample_tags: list[set[str]] = self.tags_fetcher.fetch_tags(workflow).sample_tags
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

    def _get_analysis_sample_delivery_files(self, case: Case) -> list[SampleFile]:
        """Return a all sample files to deliver for a case."""
        sample_ids: list[str] = case.sample_ids
        delivery_files: list[SampleFile] = []
        for sample_id in sample_ids:
            sample_delivery_files: list[SampleFile] = self._get_sample_files_from_case_bundle(
                case_id=case.internal_id, sample_id=sample_id, workflow=case.data_analysis
            )
            delivery_files.extend(sample_delivery_files)
        return delivery_files

    def get_analysis_case_delivery_files(self, case: Case) -> list[CaseFile]:
        """
        Return a complete list of analysis case files to be delivered and ignore analysis sample
        files.
        """
        case_tags: list[set[str]] = self.tags_fetcher.fetch_tags(case.data_analysis).case_tags
        sample_id_tags: list[str] = case.sample_ids
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
