from cg.constants.delivery import PIPELINE_ANALYSIS_TAG_MAP
from cg.services.file_delivery.fetch_delivery_files_tags.fetch_delivery_file_tags_service import (
    FetchDeliveryFileTagsService,
)
from cg.services.file_delivery.fetch_delivery_files_tags.models import DeliveryFileTags


class FetchAnalysisDeliveryFileTagsService(FetchDeliveryFileTagsService):

    def fetch_tags(self, workflow: str) -> DeliveryFileTags:
        """Get the case tags for the files that need to be delivered for a workflow."""
        return DeliveryFileTags(
            case_tags=PIPELINE_ANALYSIS_TAG_MAP[workflow]["case_tags"],
            sample_tags=PIPELINE_ANALYSIS_TAG_MAP[workflow]["sample_tags"],
        )
