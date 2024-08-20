from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import Workflow
from cg.services.file_delivery.fetch_delivery_files_tags.fetch_fastq_delivery_file_tags_service import (
    FetchFastqDeliveryFileTagsService,
)
from cg.services.file_delivery.fetch_file_service.fetch_delivery_files_service import (
    FetchDeliveryFilesService,
)
from cg.services.file_delivery.fetch_file_service.models import SampleFile, DeliveryFiles
from cg.store.exc import EntryNotFoundError
from cg.store.models import Case
from cg.store.store import Store
from housekeeper.store.models import File


class FetchFastqDeliveryFilesService(FetchDeliveryFilesService):
    """
    Fetch the fastq files for a case from Housekeeper.
    """

    def __init__(
        self,
        status_db: Store,
        hk_api: HousekeeperAPI,
        tags_fetcher: FetchFastqDeliveryFileTagsService,
    ):
        self.status_db = status_db
        self.hk_api = hk_api
        self.tags_fetcher = tags_fetcher

    def get_files_to_deliver(self, case_id: str) -> DeliveryFiles:
        """Return a list of FASTQ files to be delivered for a case and its samples."""
        case: Case = self.status_db.get_case_by_internal_id(internal_id=case_id)
        sample_ids: list[str] = case.sample_ids
        fastq_files: list[SampleFile] = []
        for sample_id in sample_ids:
            fastq_files.extend(
                self._get_fastq_files_for_sample(sample_id=sample_id, case_id=case_id)
            )
        return DeliveryFiles(case_files=None, sample_files=fastq_files)

    def _get_fastq_files_for_sample(self, case_id: str, sample_id: str) -> list[SampleFile]:
        """Get the FASTQ files for a sample."""
        fastq_tags: list[set[str]] = self.tags_fetcher.fetch_tags(Workflow.FASTQ).sample_tags
        fastq_files: list[File] = self.hk_api.get_files_from_latest_version_containing_tags(
            bundle_name=sample_id, tags=fastq_tags
        )
        return [
            SampleFile(case_id=case_id, sample_id=sample_id, file_path=fastq_file.full_path)
            for fastq_file in fastq_files
        ]
