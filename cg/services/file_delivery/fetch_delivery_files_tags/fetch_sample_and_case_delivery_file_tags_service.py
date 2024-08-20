from cg.constants import Workflow
from cg.constants.delivery import PIPELINE_ANALYSIS_TAG_MAP
from cg.services.file_delivery.fetch_delivery_files_tags.error_handling import (
    handle_tag_fetch_errors,
)
from cg.services.file_delivery.fetch_delivery_files_tags.fetch_delivery_file_tags_service import (
    FetchDeliveryFileTagsService,
)
from cg.services.file_delivery.fetch_delivery_files_tags.models import DeliveryFileTags


class FetchSampleAndCaseDeliveryFileTagsService(FetchDeliveryFileTagsService):

    @handle_tag_fetch_errors
    def fetch_tags(self, workflow: Workflow) -> DeliveryFileTags:
        """Get the case tags for the files that need to be delivered for a workflow."""
        self._validate_workflow(workflow)
        return DeliveryFileTags(
            case_tags=PIPELINE_ANALYSIS_TAG_MAP[workflow]["case_tags"],
            sample_tags=PIPELINE_ANALYSIS_TAG_MAP[workflow]["sample_tags"],
        )

    @staticmethod
    def _validate_workflow(workflow: Workflow):
        """Validate the workflow."""
        if workflow not in PIPELINE_ANALYSIS_TAG_MAP:
            raise ValueError(f"Workflow {workflow} is not supported.")
        return workflow
